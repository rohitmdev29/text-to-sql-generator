# Text-to-SQL Generator

A Text-to-SQL system that takes a question in plain English and returns an
executable SQL query. Built by fine-tuning Google's Gemma-2B model on a
large Text-to-SQL dataset, then deploying it through a Streamlit interface
with Ollama running the model locally.

This started as a learning project. I wanted to understand what it actually
takes to fine-tune an LLM, quantize it, and put it in front of real users —
not just get a model to output SQL in a notebook. Most of the interesting
problems showed up after training: merging adapters, GGUF conversion, and
getting inference to work reliably on a CPU-only machine.

---

## What It Does

Given a database schema and a question, the model generates a SQL query
that can be executed directly.

**Input:**

    Schema:
    CREATE TABLE customers (id INT, name TEXT, city TEXT);
    CREATE TABLE orders (id INT, customer_id INT, total REAL, order_date DATE);

    Question:
    Top 5 customers by total spending

**Output:**

    SELECT c.name, SUM(o.total) AS total_spending
    FROM customers c
    JOIN orders o ON c.id = o.customer_id
    GROUP BY c.id, c.name
    ORDER BY total_spending DESC
    LIMIT 5;

The generated query is executed against a SQLite database, and the results
are shown in a table that can be downloaded as CSV.

---

## How It Works

    Natural Language Question
            |
            v
       Streamlit UI
            |
            v
       Inference Backend
       (Ollama locally, Groq API on cloud)
            |
            v
       Generated SQL
            |
            v
       SQLite Database
            |
            v
       Query Results

The pipeline has three parts:

1. **Training** — Gemma-2B is fine-tuned with QLoRA on ~78,000 Text-to-SQL
   examples. Only 0.79% of the model's parameters are trained.

2. **Deployment** — The LoRA adapter is merged back into the base model,
   quantized to 8-bit GGUF, and served through Ollama on the local machine.

3. **Application** — A Streamlit front-end lets the user pick a preset question
   or type their own, generates SQL through the inference backend, and runs
   the query against a sample e-commerce database.

---

## Results

I evaluated the model on a 20-question held-out test set using exact match
accuracy. The base Gemma-2B model scored 0% — it doesn't understand SQL
syntax or the schema structure well enough to produce valid queries out of
the box. After fine-tuning, the same model scored 80%.

| Metric                    | Base Model | Fine-Tuned Model |
| :------------------------ | :--------- | :--------------- |
| Exact Match Accuracy      | 0%         | 80%              |
| Trainable Parameters      | 100%       | 0.79%            |
| Model Size (8-bit GGUF)   | —          | 2.59 GB          |
| Training Time             | —          | ~10 min on T4    |

A few notes on these numbers:

- "Exact match" is strict — the generated SQL has to match the reference
  query character-for-character after normalization. The 80% figure is honest,
  not cherry-picked.
- The 0% baseline isn't a bug. The base model has no idea what a SELECT
  statement looks like in this format.
- Training only took 10 minutes because QLoRA keeps the base model frozen
  in 4-bit and trains a tiny set of adapters on top.

---

## Tech Stack

| Layer            | Technology                          |
| :--------------- | :---------------------------------- |
| Base Model       | Google Gemma-2B (instruction-tuned) |
| Fine-Tuning      | QLoRA (4-bit), Unsloth, Hugging Face TRL |
| Dataset          | b-mc2/sql-create-context (78K rows) |
| Quantization     | GGUF (Q8_0)                         |
| Local Inference  | Ollama                              |
| Cloud Inference  | Groq API (Llama 3.3 / GPT-OSS 120B) |
| UI               | Streamlit                           |
| Database         | SQLite                              |
| Language         | Python                              |

---

## Setting It Up

### Prerequisites

- Python 3.10 or later
- Ollama installed ([ollama.com/download](https://ollama.com/download))
- A Groq API key for cloud deployment ([console.groq.com](https://console.groq.com))

### Local Setup

Clone the repository and set up a virtual environment:

    git clone https://github.com/rohitmdev29/text-to-sql-generator.git
    cd text-to-sql-generator
    python -m venv venv
    venv\Scripts\activate         # Windows
    source venv/bin/activate      # macOS / Linux

Install the dependencies:

    pip install -r requirements.txt

Create the sample database:

    python create_db.py

Set up the API key. Create a file at `.streamlit/secrets.toml`:

    GROQ_API_KEY = "your_groq_api_key_here"

Run the app:

    streamlit run app.py

The app will open at `http://localhost:8501`.

### Running the Fine-Tuned Model Locally (Optional)

If you want to use the fine-tuned Gemma model instead of the Groq backend,
download the GGUF file from Hugging Face:

    https://huggingface.co/rmehra007/gemma-sql-merged-GGUF

Then create a Modelfile:

    FROM ./gemma-sql-merged-q8_0.gguf

    TEMPLATE """### Schema:
    {{ .Prompt }}

    ### SQL Query:
    """

    PARAMETER temperature 0
    PARAMETER stop "<eos>"

Import it into Ollama:

    ollama create sql-gemma -f Modelfile
    ollama run sql-gemma

---

## Project Structure

    text-to-sql-generator/
    |-- app.py                  Streamlit application
    |-- create_db.py            Creates the sample e-commerce database
    |-- merge_lora.py           Merges the LoRA adapter into the base model
    |-- Modelfile               Ollama configuration
    |-- requirements.txt        Python dependencies
    |-- .gitignore
    |-- README.md
    |-- screenshots/            Demo screenshots

---

## Training Details

For anyone who wants to reproduce this.

| Parameter             | Value                                                  |
| :-------------------- | :----------------------------------------------------- |
| Base Model            | google/gemma-2-2b-it                                   |
| Method                | QLoRA (4-bit NF4 quantization)                         |
| LoRA Rank (r)         | 16                                                     |
| LoRA Alpha            | 16                                                     |
| Target Modules        | q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj |
| Learning Rate         | 2e-4                                                   |
| Batch Size            | 2 (with gradient accumulation of 4)                    |
| Max Steps             | 300                                                    |
| Warmup Steps          | 5                                                      |
| Optimizer             | AdamW 8-bit                                            |
| Hardware              | Single NVIDIA T4 (15 GB VRAM)                          |
| Trainable Parameters  | 20.77M out of 2.63B (0.79%)                            |

Training was done on Google Colab with Unsloth for faster throughput. The
merge and GGUF conversion were done separately on a CPU-only setup after the
Colab GPU quota expired.







## Links

- **GitHub Repository:** [github.com/rohitmdev29/text-to-sql-generator](https://github.com/rohitmdev29/text-to-sql-generator)
- **LoRA Adapter:** [rmehra007/gemma-sql-lora](https://huggingface.co/rmehra007/gemma-sql-lora)
- **Merged Model:** [rmehra007/gemma-sql-merged](https://huggingface.co/rmehra007/gemma-sql-merged)
- **GGUF Model:** [rmehra007/gemma-sql-merged-GGUF](https://huggingface.co/rmehra007/gemma-sql-merged-GGUF)

---

## License

MIT License. Use it however you want.
