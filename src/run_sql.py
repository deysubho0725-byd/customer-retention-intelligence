# run_sql.py
# Small helper: runs every query in a .sql file and prints the results.
#
# How to use:
#     python src/run_sql.py sql/01_first_look.sql

import sys
import duckdb

# The .sql file name comes from the command line
sql_file = sys.argv[1]

# Read the whole file as text
with open(sql_file) as f:
    sql_text = f.read()

con = duckdb.connect("data/retail.duckdb")

# Queries are separated by semicolons, so split on ";"
queries = sql_text.split(";")

for query in queries:
    # Separate the comment lines (starting with --) from the actual SQL
    lines = query.split("\n")
    comments = [line for line in lines if line.strip().startswith("--")]
    sql_only = "\n".join(line for line in lines if not line.strip().startswith("--")).strip()

    # Skip empty bits (like the space after the last semicolon)
    if sql_only == "":
        continue

    # If there's a question comment like "-- Q1: ...", print it as a title
    for c in comments:
        if c.strip().startswith("-- Q"):
            print("=====", c.strip()[3:], "=====")

    result = con.execute(sql_only)

    # SELECT queries give back a table, so print it.
    # Things like CREATE VIEW don't, so just confirm they ran.
    if sql_only.upper().startswith("SELECT") or sql_only.upper().startswith("WITH"):
        print(result.df().to_string(index=False))
    else:
        print("Done:", sql_only.split("\n")[0])
    print()

con.close()