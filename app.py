# ============================================
# Text-to-SQL Streamlit Application
# Author: Rohit Mehra
# Created: August 2025
#
# Front-end for the Text-to-SQL system. The fine-tuned Gemma-2B
# model is deployed locally via Ollama. For cloud deployment,
# the app uses the Groq API as an inference backend.
#
# Generated SQL is executed against a local SQLite database.
#
# Environment variables required:
#   GROQ_API_KEY  - Groq API key (free tier available)
# ============================================

import streamlit as st
import sqlite3
import pandas as pd
import time
import os
from groq import Groq

# ---------- Configuration ----------
DB_FILE = "ecommerce.db"
GROQ_MODEL = "openai/gpt-oss-120b"
MAX_NEW_TOKENS = 300
REQUEST_TIMEOUT = 60  # seconds


# ---------- Auto-create database if missing ----------
if not os.path.exists(DB_FILE):
    import subprocess
    subprocess.run(["python", "create_db.py"], check=False)

# ---------- Preset Queries ----------
PRESET_QUERIES = [
    "Select a query...",
    "Top 5 customers by total spending",
    "Total revenue per product category",
    "Average order value per city",
    "Latest 10 orders with customer names",
    "Products with stock less than 50",
    "Count of orders by status",
    "Top 5 best-selling products by quantity",
    "Monthly sales trend for the last 12 months",
    "Customers who haven't placed any orders",
    "Total revenue from delivered orders only",
]

st.set_page_config(
    page_title="Text-to-SQL Generator",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)


# ---------- Custom Styling ----------
st.markdown("""
    <style>
    /* ---- Global background ---- */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf3 100%);
    }

    /* ---- Title ---- */
    h1 {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 50%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }

    /* ---- Subheaders ---- */
    h2, h3 {
        color: #1e3a8a !important;
        font-weight: 700 !important;
    }

    /* ---- Primary button ---- */
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(59, 130, 246, 0.5);
    }

    /* ---- Secondary button ---- */
    .stButton > button[kind="secondary"] {
        background: linear-gradient(90deg, #10b981 0%, #059669 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }

    /* ---- Text area ---- */
    .stTextArea textarea {
        border: 2px solid #cbd5e1;
        border-radius: 10px;
        font-size: 15px;
        transition: border-color 0.3s;
    }
    .stTextArea textarea:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
    }

    /* ---- Code block ---- */
    .stCodeBlock {
        border-radius: 10px;
        border: 1px solid #334155;
    }

    /* ---- Sidebar ---- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f1f5f9 100%);
        border-right: 1px solid #e2e8f0;
    }

    /* ---- Expander ---- */
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, #eff6ff 0%, #dbeafe 100%);
        border-radius: 8px;
        font-weight: 600;
        color: #1e40af;
    }

    /* ---- Alerts ---- */
    .stAlert {
        border-radius: 10px;
    }

    /* ---- Caption ---- */
    .stCaption {
        color: #64748b;
        font-weight: 500;
    }

    /* ---- Divider ---- */
    hr {
        border-color: #cbd5e1;
        opacity: 0.5;
    }

    /* ---- Preset dropdown ---- */
    div[data-baseweb="select"] > div {
        border: 2px solid #cbd5e1 !important;
        border-radius: 10px !important;
        background-color: #ffffff !important;
    }
    div[data-baseweb="select"] > div:hover {
        border-color: #3b82f6 !important;
    }

    /* ---- Dataframe container ---- */
    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
        border: 1px solid #e2e8f0 !important;
        margin-top: 8px !important;
        margin-bottom: 24px !important;
    }

    /* ---- Dataframe cells ---- */
    .stDataFrame [role="gridcell"] {
        padding: 12px 16px !important;
        font-size: 14px !important;
    }

    /* ---- Dataframe header ---- */
    .stDataFrame [role="columnheader"] {
        background-color: #f1f5f9 !important;
        font-weight: 700 !important;
        color: #1e293b !important;
        padding: 14px 16px !important;
        font-size: 13px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }

    /* ---- Success message ---- */
    .stSuccess {
        border-radius: 10px !important;
        padding: 12px 16px !important;
        margin-bottom: 12px !important;
    }

    /* ---- Results heading ---- */
    .results-heading {
        color: #1e3a8a;
        font-size: 1.4rem;
        font-weight: 700;
        margin-top: 12px;
        margin-bottom: 4px;
        letter-spacing: -0.3px;
    }

    /* ---- Download button ---- */
    .stDownloadButton > button {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25) !important;
        transition: all 0.3s ease !important;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4) !important;
    }
    </style>
""", unsafe_allow_html=True)


# ---------- Secrets Loading ----------
def load_api_key():
    """Reads the Groq API key from Streamlit secrets or environment variables."""
    try:
        key = st.secrets["GROQ_API_KEY"]
    except (KeyError, FileNotFoundError):
        key = os.getenv("GROQ_API_KEY")

    if not key:
        return None, "GROQ_API_KEY not found. Add it to Streamlit secrets or environment variables."
    return key, None


# ---------- Database Helpers ----------
def get_schema():
    """Reads table definitions from the SQLite database."""
    if not os.path.exists(DB_FILE):
        return None, "Database file not found. Run create_db.py first."

    db = sqlite3.connect(DB_FILE)
    cur = db.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cur.fetchall()]

    schema_parts = []
    for table in tables:
        cur.execute(f"PRAGMA table_info({table})")
        columns = cur.fetchall()
        col_defs = [f"{col[1]} {col[2]}" for col in columns]
        schema_parts.append(f"CREATE TABLE {table} ({', '.join(col_defs)});")

    db.close()
    return "\n".join(schema_parts), None


def run_query(sql):
    """Executes a SQL query and returns the result as a DataFrame."""
    db = sqlite3.connect(DB_FILE)
    try:
        df = pd.read_sql_query(sql, db)
        return df, None
    except Exception as e:
        return None, str(e)
    finally:
        db.close()


# ---------- Model Helpers ----------
def clean_sql_output(raw_text):
    """Removes markdown formatting and prompt echoes from the model output."""
    text = raw_text.strip()

    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    if "<eos>" in text:
        text = text.split("<eos>")[0].strip()

    if "###" in text:
        text = text.split("###")[0].strip()

    for keyword in ["SELECT", "WITH", "INSERT", "UPDATE", "DELETE"]:
        idx = text.upper().find(keyword)
        if idx != -1:
            text = text[idx:]
            break

    text = text.rstrip()
    if text.endswith(";"):
        text = text[:-1]

    return text.strip() + ";"


def generate_sql(question, schema, api_key):
    """Sends the question to Groq API and returns the generated SQL."""
    client = Groq(api_key=api_key, timeout=REQUEST_TIMEOUT)

    system_prompt = (
        "You are an expert SQL query generator. "
        "Given a database schema and a natural language question, "
        "return ONLY a single valid SQLite SQL query. "
        "Do not include explanations, markdown fences, or any text outside the SQL query."
    )

    user_prompt = f"""### Schema:
{schema}

### Question:
{question}

### SQL Query:
"""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=MAX_NEW_TOKENS
        )
        raw = response.choices[0].message.content
        return clean_sql_output(raw), None
    except Exception as e:
        return None, f"Model request failed: {type(e).__name__} - {str(e)}"


# ---------- Callbacks ----------
def apply_preset():
    """Copies the selected preset query into the question text area."""
    preset = st.session_state.get("preset_selector", "")
    if preset and preset != "Select a query...":
        st.session_state.question_input = preset


# ---------- Session State ----------
if "generated_sql" not in st.session_state:
    st.session_state.generated_sql = None
if "generation_time" not in st.session_state:
    st.session_state.generation_time = None
if "error" not in st.session_state:
    st.session_state.error = None
if "query_results" not in st.session_state:
    st.session_state.query_results = None
if "query_error" not in st.session_state:
    st.session_state.query_error = None
if "question_input" not in st.session_state:
    st.session_state.question_input = ""


# ---------- UI Layout ----------
st.title("Text-to-SQL Generator")
st.caption("Fine-tuned Gemma-2B · QLoRA · 8-bit GGUF · Groq Inference Backend")

api_key, key_error = load_api_key()
schema, schema_error = get_schema()

if key_error:
    st.error(key_error)
    st.stop()

if schema_error:
    st.error(schema_error)
    st.stop()


# ---- Sidebar: database schema ----
with st.sidebar:
    st.header("Database Schema")

    db = sqlite3.connect(DB_FILE)
    cur = db.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    table_names = [r[0] for r in cur.fetchall()]

    for tname in table_names:
        cur.execute(f"SELECT COUNT(*) FROM {tname}")
        row_count = cur.fetchone()[0]

        with st.expander(f"{tname} ({row_count} rows)", expanded=False):
            cur.execute(f"PRAGMA table_info({tname})")
            for col in cur.fetchall():
                st.text(f"  {col[1]}  {col[2]}")

    db.close()


# ---- Row 1: Question (left) + Generated SQL (right) ----
col_input, col_output = st.columns([1, 1.2], gap="large")

with col_input:
    st.markdown("### Question")

    # Preset queries dropdown (auto-fills text area via callback)
    st.markdown("**Quick Select (Preset Queries)**")
    st.selectbox(
        "Choose a sample question:",
        options=PRESET_QUERIES,
        key="preset_selector",
        on_change=apply_preset,
        label_visibility="collapsed"
    )

    # Editable text area — user can type or modify preset
    question = st.text_area(
        "Or type your own question:",
        height=110,
        placeholder="Example: Which 5 customers have spent the most money?",
        key="question_input"
    )

    generate_clicked = st.button(
        "Generate SQL",
        type="primary",
        use_container_width=True
    )

    if generate_clicked:
        if not question.strip():
            st.warning("Please enter a question first.")
        else:
            with st.spinner("Generating SQL..."):
                start = time.time()
                sql, err = generate_sql(question, schema, api_key)
                elapsed = time.time() - start

            if err:
                st.session_state.error = err
                st.session_state.generated_sql = None
            else:
                st.session_state.generated_sql = sql
                st.session_state.generation_time = elapsed
                st.session_state.error = None
                st.session_state.query_results = None
                st.session_state.query_error = None


with col_output:
    st.markdown("### Generated SQL")

    if st.session_state.error:
        st.error(st.session_state.error)

    elif st.session_state.generated_sql:
        st.code(st.session_state.generated_sql, language="sql")

        if st.session_state.generation_time:
            st.caption(f"Generated in {st.session_state.generation_time:.2f} seconds")

        run_clicked = st.button(
            "Run on Database",
            use_container_width=True,
            key="run_query_btn"
        )

        if run_clicked:
            with st.spinner("Running query..."):
                df, err = run_query(st.session_state.generated_sql)
            if err:
                st.session_state.query_results = None
                st.session_state.query_error = err
            else:
                st.session_state.query_results = df
                st.session_state.query_error = None
    else:
        st.info("Select a preset question or type your own, then click Generate SQL.")


# ---- Row 2: Results table (full width) ----
if st.session_state.get("query_results") is not None:
    st.markdown("---")

    df = st.session_state.query_results

    # Header row: heading + row count + download button
    head_col1, head_col2 = st.columns([3, 1])

    with head_col1:
        st.markdown(
            f'<div class="results-heading">Query Results '
            f'<span style="color: #64748b; font-size: 0.9rem; font-weight: 500;">'
            f'({len(df)} rows × {len(df.columns)} columns)</span></div>',
            unsafe_allow_html=True
        )

    with head_col2:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="query_results.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Column config for better number/date formatting
    column_config = {}
    for col in df.columns:
        col_lower = col.lower()
        if any(k in col_lower for k in ["total", "price", "revenue", "spent", "amount", "value"]):
            column_config[col] = st.column_config.NumberColumn(col, format="₹%.2f")
        elif "date" in col_lower:
            column_config[col] = st.column_config.DateColumn(col, format="YYYY-MM-DD")
        elif any(k in col_lower for k in ["quantity", "count", "stock", "id"]):
            column_config[col] = st.column_config.NumberColumn(col, format="%d")

    # Render table with proper spacing
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=min(450, (len(df) + 1) * 38 + 20),
        column_config=column_config if column_config else None
    )

elif st.session_state.get("query_error"):
    st.markdown("---")
    st.error(f"Query failed: {st.session_state.query_error}")


# ---------- Footer ----------
st.markdown("---")
st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #06b6d4 100%);
        padding: 28px 32px;
        border-radius: 14px;
        margin-top: 20px;
        box-shadow: 0 8px 24px rgba(30, 58, 138, 0.25);
        text-align: center;
    ">
        <div style="
            color: #ffffff;
            font-size: 22px;
            font-weight: 800;
            letter-spacing: 0.3px;
            margin-bottom: 10px;
        ">
            Model: Gemma-2B Fine-Tuned with QLoRA
        </div>
        <div style="
            color: #dbeafe;
            font-size: 17px;
            font-weight: 500;
            margin-bottom: 18px;
        ">
            Trained on 78,000+ Text-to-SQL examples &nbsp;·&nbsp; 8-bit GGUF &nbsp;·&nbsp; Deployed via Groq Inference Backend
        </div>
        <div style="
            display: inline-block;
            background: rgba(255, 255, 255, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.3);
            padding: 10px 24px;
            border-radius: 30px;
            backdrop-filter: blur(10px);
        ">
            <a href="https://github.com/rohitmdev29/text-to-sql-generator" 
               target="_blank"
               style="
                   color: #ffffff;
                   font-size: 16px;
                   font-weight: 700;
                   text-decoration: none;
                   letter-spacing: 0.5px;
               ">
                🔗 github.com/rohitmdev29/text-to-sql-generator
            </a>
        </div>
    </div>
""", unsafe_allow_html=True)