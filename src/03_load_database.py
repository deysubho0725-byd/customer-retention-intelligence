# 03_load_database.py
# Load the clean CSV files into a DuckDB database,
# so we can do the rest of the analysis in SQL.

import duckdb

# Connect to the database file (it gets created if it doesn't exist)
con = duckdb.connect("data/retail.duckdb")

# ---- 1. Transactions table ----
# Rename columns so they're easy to use in SQL
# ("Customer ID" has a space, which is annoying to type every time)
con.execute("""
    CREATE OR REPLACE TABLE transactions AS
    SELECT
        Invoice        AS invoice,
        StockCode      AS stock_code,
        Description    AS description,
        Quantity       AS quantity,
        InvoiceDate    AS invoice_date,
        Price          AS price,
        "Customer ID"  AS customer_id,
        Country        AS country,
        Revenue        AS revenue
    FROM read_csv_auto('data/clean/transactions.csv')
""")

# ---- 2. Cancellations table ----
con.execute("""
    CREATE OR REPLACE TABLE cancellations AS
    SELECT
        Invoice                  AS invoice,
        StockCode                AS stock_code,
        Quantity                 AS quantity,
        InvoiceDate              AS invoice_date,
        Price                    AS price,
        CAST("Customer ID" AS INTEGER) AS customer_id,
        Country                  AS country
    FROM read_csv_auto('data/clean/cancellations.csv')
""")

# ---- 3. Quick check that everything loaded ----
print("Transactions table:")
print(con.execute("""
    SELECT
        COUNT(*)                     AS total_rows,
        COUNT(DISTINCT customer_id)  AS customers,
        ROUND(SUM(revenue), 2)       AS total_revenue
    FROM transactions
""").df())

print("\nCancellations table:")
print(con.execute("SELECT COUNT(*) AS total_rows FROM cancellations").df())

# Always close the connection when done
con.close()
print("\nDatabase saved to data/retail.duckdb")