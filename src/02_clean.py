# 02_clean.py
# Clean the Online Retail II data and save it as CSV files.
# Each cleaning step prints how many rows it removed, so we can
# explain every decision in the README.

import os
import pandas as pd

# ---- 1. Load the data (same as before) ----
print("Loading the Excel file... (this can take 1-3 minutes)")

sheets = pd.read_excel(
    "data/raw/online_retail_II.xlsx",
    sheet_name=None,
    dtype={"Invoice": str, "StockCode": str}
)
df = pd.concat(sheets.values(), ignore_index=True)

print("Starting rows:", len(df))


# ---- 2. Save cancellations separately ----
# We don't throw these away. Customers who return a lot might be
# unhappy, so we'll test this as a churn signal later.
# We only keep cancellations where we know the customer.
cancellations = df[df["Invoice"].str.startswith("C") & df["Customer ID"].notna()]
print("Cancellations saved for later:", len(cancellations))


# ---- 3. Cleaning, one step at a time ----
print("\n===== CLEANING STEPS =====")

# Step A: remove rows with no Customer ID
# (we can't track a customer we can't identify)
before = len(df)
df = df[df["Customer ID"].notna()]
print("A. Removed missing Customer ID:", before - len(df))

# Step B: remove cancelled invoices (they start with "C")
before = len(df)
df = df[~df["Invoice"].str.startswith("C")]
print("B. Removed cancellations:", before - len(df))

# Step C: remove zero/negative quantity (stock adjustments, damages)
before = len(df)
df = df[df["Quantity"] > 0]
print("C. Removed zero/negative quantity:", before - len(df))

# Step D: remove zero/negative price (free items, admin entries)
before = len(df)
df = df[df["Price"] > 0]
print("D. Removed zero/negative price:", before - len(df))

# Step E: remove non-product codes like POST (postage) or M (manual)
# Real product codes start with 5 digits, e.g. "85048" or "79323P"
before = len(df)
is_product = df["StockCode"].str[:5].str.isdigit()

# Show which non-product codes we're removing, so we can check them
print("   Non-product codes found:")
print(df[~is_product]["StockCode"].value_counts().head(10))

df = df[is_product]
print("E. Removed non-product codes:", before - len(df))

# Step F: remove exact duplicate rows
before = len(df)
df = df.drop_duplicates()
print("F. Removed duplicates:", before - len(df))


# ---- 4. Small tidy ups ----
# Customer ID loads as a decimal (13085.0), make it a whole number
df["Customer ID"] = df["Customer ID"].astype(int)

# Revenue for each line = quantity x price
df["Revenue"] = df["Quantity"] * df["Price"]


# ---- 5. Final summary ----
print("\n===== AFTER CLEANING =====")
print("Rows left:", len(df))
print("Customers:", df["Customer ID"].nunique())
print("Invoices:", df["Invoice"].nunique())
print("Total revenue (GBP):", round(df["Revenue"].sum(), 2))


# ---- 6. Save the clean data ----
# Make the folder if it doesn't exist yet
os.makedirs("data/clean", exist_ok=True)

df.to_csv("data/clean/transactions.csv", index=False)
cancellations.to_csv("data/clean/cancellations.csv", index=False)

print("\nSaved data/clean/transactions.csv and data/clean/cancellations.csv")