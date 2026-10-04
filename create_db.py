# ============================================
# E-commerce Database Setup Script
# Author: Rohit Mehra

# 
# I built this script to create a sample e-commerce database
# with customers, products, and orders. I made this because 
# I needed real data to test my Text-to-SQL model — testing
# on synthetic datasets wasn't giving me the full picture.
# ============================================

import sqlite3
import random
import os
from datetime import datetime, timedelta

DB_FILE = "ecommerce.db"

# Indian cities for customer locations
cities_list = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata',
               'Hyderabad', 'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow']

# Common Indian names — will combine randomly
first_names = ['Rahul', 'Priya', 'Amit', 'Sneha', 'Vikram', 'Anjali',
               'Rohan', 'Divya', 'Karan', 'Pooja', 'Arjun', 'Neha',
               'Aditya', 'Riya', 'Siddharth', 'Kavya', 'Nikhil', 'Ananya']

last_names = ['Sharma', 'Verma', 'Patel', 'Singh', 'Kumar', 'Reddy',
              'Gupta', 'Mehta', 'Joshi', 'Nair', 'Iyer', 'Chopra']

# Product categories and their items
categories_dict = {
    'Electronics': ['Wireless Earbuds', 'Smartphone', 'Laptop', 'Smartwatch',
                    'Bluetooth Speaker', 'Power Bank', 'Tablet', 'Camera'],
    'Clothing': ['T-Shirt', 'Jeans', 'Jacket', 'Saree', 'Kurta', 'Shoes',
                 'Dress', 'Hoodie'],
    'Books': ['Python Guide', 'Data Science Book', 'AI Handbook',
              'Novel', 'Biography', 'Self-Help Book'],
    'Home & Kitchen': ['Blender', 'Coffee Maker', 'Cookware Set',
                       'Bed Sheets', 'Table Lamp', 'Wall Clock'],
    'Sports': ['Cricket Bat', 'Football', 'Yoga Mat', 'Dumbbells',
               'Badminton Racket', 'Running Shoes'],
    'Beauty': ['Face Cream', 'Perfume', 'Lipstick', 'Hair Oil', 'Sunscreen'],
    'Toys': ['Building Blocks', 'Remote Car', 'Puzzle', 'Board Game',
             'Action Figure'],
    'Groceries': ['Rice', 'Oil', 'Tea', 'Coffee', 'Snacks', 'Spices']
}

# Price ranges per category — keeps things realistic
price_ranges = {
    'Electronics': (1500, 80000),
    'Clothing': (300, 3000),
    'Books': (150, 1500),
    'Home & Kitchen': (500, 15000),
    'Sports': (400, 10000),
    'Beauty': (200, 2500),
    'Toys': (300, 5000),
    'Groceries': (50, 800)
}


def setup_database():
    """Main function — creates tables and inserts all data."""
    
    print("Setting up database... this might take a moment\n")
    
    # Clean up old db file if it exists
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"Removed old '{DB_FILE}'")
    
    # Connect to DB
    db = sqlite3.connect(DB_FILE)
    cur = db.cursor()
    
    # ---- CREATE TABLES ----
    print("Creating tables...")
    
    # Customers table
    cur.execute("""
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            city TEXT NOT NULL,
            signup_date DATE NOT NULL
        )
    """)
    
    # Products table
    cur.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL,
            rating REAL
        )
    """)
    
    # Orders table — this is the main one
    cur.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            order_date DATE NOT NULL,
            total REAL NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)
    
    print("  3 tables created (customers, products, orders)\n")
    
    # ---- INSERT CUSTOMERS (200) ----
    print("Adding customers...")
    
    customer_rows = []
    emails_used = set()
    
    for cid in range(1, 201):
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        full_name = fname + " " + lname
        
        # Email must be unique
        while True:
            em = fname.lower() + "." + lname.lower() + str(cid) + "@email.com"
            if em not in emails_used:
                emails_used.add(em)
                break
        
        city = random.choice(cities_list)
        
        # Signup between 1 month and 3 years ago
        days_back = random.randint(30, 1095)
        signup = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        customer_rows.append((cid, full_name, em, city, signup))
    
    cur.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?)", customer_rows)
    print(f"  {len(customer_rows)} customers added\n")
    
    # ---- INSERT PRODUCTS ----
    print("Adding products...")
    
    product_rows = []
    pid = 1
    
    for cat, items in categories_dict.items():
        low, high = price_ranges[cat]
        for item_name in items:
            price = round(random.uniform(low, high), 2)
            stock_qty = random.randint(0, 500)
            rate = round(random.uniform(3.0, 5.0), 1)
            
            product_rows.append((pid, item_name, cat, price, stock_qty, rate))
            pid += 1
    
    cur.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?)", product_rows)
    print(f"  {len(product_rows)} products added\n")
    
    # ---- INSERT ORDERS (1000) ----
    print("Adding orders...")
    
    order_rows = []
    statuses = ['Delivered', 'Shipped', 'Pending', 'Cancelled']
    # Most orders should be delivered — realistic distribution
    status_weights = [60, 20, 15, 5]
    
    for oid in range(1, 1001):
        cust_id = random.randint(1, 200)
        prod_id = random.randint(1, len(product_rows))
        qty = random.randint(1, 5)
        
        # Get product price to calculate total
        cur.execute("SELECT price FROM products WHERE id = ?", (prod_id,))
        unit_price = cur.fetchone()[0]
        total_amt = round(unit_price * qty, 2)
        
        # Order date — random within last 2 years
        days_ago = random.randint(0, 730)
        odate = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        stat = random.choices(statuses, weights=status_weights, k=1)[0]
        
        order_rows.append((oid, cust_id, prod_id, qty, odate, total_amt, stat))
    
    cur.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?)", order_rows)
    print(f"  {len(order_rows)} orders added\n")
    
    # ---- CREATE INDEXES (makes queries faster) ----
    print("Creating indexes...")
    cur.execute("CREATE INDEX idx_ord_cust ON orders(customer_id)")
    cur.execute("CREATE INDEX idx_ord_prod ON orders(product_id)")
    cur.execute("CREATE INDEX idx_ord_date ON orders(order_date)")
    cur.execute("CREATE INDEX idx_cust_city ON customers(city)")
    cur.execute("CREATE INDEX idx_prod_cat ON products(category)")
    print("  5 indexes created\n")
    
    db.commit()
    db.close()
    
    # ---- SUMMARY ----
    print("=" * 55)
    print("DATABASE IS READY!")
    print("=" * 55)
    print(f"  File name:  {DB_FILE}")
    print(f"  Customers:  {len(customer_rows)}")
    print(f"  Products:   {len(product_rows)}")
    print(f"  Orders:     {len(order_rows)}")
    print("=" * 55)
    print("\nNow run app.py to launch the Streamlit UI.\n")


def show_preview():
    """Displays a quick preview of the database."""
    
    print("=" * 55)
    print("DATABASE PREVIEW")
    print("=" * 55)
    
    db = sqlite3.connect(DB_FILE)
    cur = db.cursor()
    
    # Sample customers
    print("\nSample Customers:")
    cur.execute("SELECT id, name, city FROM customers LIMIT 3")
    for r in cur.fetchall():
        print(f"  {r[0]} - {r[1]} ({r[2]})")
    
    # Sample products
    print("\nSample Products:")
    cur.execute("SELECT id, name, category, price FROM products LIMIT 3")
    for r in cur.fetchall():
        print(f"  {r[0]} - {r[1]} [{r[2]}] - Rs.{r[3]}")
    
    # Sample orders
    print("\nSample Orders:")
    cur.execute("SELECT id, customer_id, product_id, total, status FROM orders LIMIT 3")
    for r in cur.fetchall():
        print(f"  Order #{r[0]}: Cust {r[1]} -> Prod {r[2]} - Rs.{r[3]} ({r[4]})")
    
    # Total revenue
    cur.execute("SELECT SUM(total) FROM orders WHERE status = 'Delivered'")
    rev = cur.fetchone()[0]
    print(f"\nTotal Revenue (Delivered orders): Rs.{rev:,.2f}")
    
    # Top 3 customers
    print("\nTop 3 Customers (by spending):")
    cur.execute("""
        SELECT c.name, SUM(o.total) as spent
        FROM customers c
        JOIN orders o ON c.id = o.customer_id
        WHERE o.status = 'Delivered'
        GROUP BY c.id
        ORDER BY spent DESC
        LIMIT 3
    """)
    for name, amount in cur.fetchall():
        print(f"  {name}: Rs.{amount:,.2f}")
    
    db.close()
    print("\n" + "=" * 55)


# Entry point
if __name__ == "__main__":
    setup_database()
    show_preview()
