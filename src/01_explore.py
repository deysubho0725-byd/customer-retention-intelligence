# 01_explore.py
# First look at the Online Retail II data.
# Goal: load both sheets, combine them, and check how messy the data is.

import pandas as pd

# ---- 1. Load the data ----
# The Excel file has two sheets (one per year).
# sheet_name=None tells pandas to read ALL sheets.
# We keep Invoice and StockCode as text, because some have letters in them (like "C489449").
print("Loading the Excel file... (this can take 1-3 minutes)")

sheets = pd.read_excel(
    "data/raw/online_retail_II.xlsx",
    sheet_name=None,
    dtype={"Invoice": str, "StockCode": str}
)

# Show how many rows are in each sheet
for sheet_name in sheets:
    print(sheet_name, "rows:", len(sheets[sheet_name]))

# Combine the two sheets into one big table
df = pd.concat(sheets.values(), ignore_index=True)


# ---- 2. Basic overview ----
print("\n===== OVERVIEW =====")
print("Total rows:", len(df))
print("First date:", df["InvoiceDate"].min())
print("Last date:", df["InvoiceDate"].max())
print("Number of customers:", df["Customer ID"].nunique())
print("Number of invoices:", df["Invoice"].nunique())

print("\n===== FIRST 5 ROWS =====")
print(df.head())


# ---- 3. Missing values ----
# How many empty cells are in each column?
print("\n===== MISSING VALUES =====")
print(df.isna().sum())


# ---- 4. Data quality checks ----
print("\n===== DATA QUALITY CHECKS =====")

# Invoices starting with "C" are cancellations (returns)
cancelled = df["Invoice"].str.startswith("C")
print("Cancelled lines:", cancelled.sum())

# Quantity should be positive for a normal sale
print("Zero or negative quantity:", (df["Quantity"] <= 0).sum())

# Price should be positive too
print("Zero or negative price:", (df["Price"] <= 0).sum())

# Rows that are exactly the same as another row
print("Duplicate rows:", df.duplicated().sum())