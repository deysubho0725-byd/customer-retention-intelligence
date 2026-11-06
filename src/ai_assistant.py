# ai_assistant.py
# AI analyst assistant: ask a business question in plain English,
# the AI writes the SQL, we run it on our customer data, and the AI
# explains the result in one or two sentences.
#
# How it works:
#   1. Your question + a description of the table go to the AI model
#   2. The AI replies with a SQL query
#   3. We check the query is safe (read-only) and run it with DuckDB
#   4. If the SQL has an error, we send the error back so the AI can fix it (once)
#   5. The AI turns the result table into a short plain-English answer
#
# Run it with:  python src/ai_assistant.py

import duckdb
import ollama

MODEL = "qwen2.5-coder:7b"


# ---- 1. Load the customer risk scores into an in-memory database ----
# In-memory means nothing is saved to disk, so the assistant can never
# change our real data.
con = duckdb.connect()
con.execute("""
    CREATE TABLE customer_risk AS
    SELECT * FROM read_csv_auto('data/customer_risk_scores.csv')
""")


# ---- 2. Describe the table for the AI ----
# The better we describe the data, the better SQL the AI writes.
# This is written by hand on purpose: plain descriptions and the exact
# values used in the text columns help the AI a lot.
TABLE_DESCRIPTION = """
Table: customer_risk
One row per current customer of a UK online gift retailer (data as of 9 Dec 2011).
Money is in GBP (pounds).

Columns:
- customer_id (integer): customer number
- country (text): customer's country. Ireland is stored as 'EIRE'. The UK is 'United Kingdom'.
- is_uk (integer): 1 if the customer is in the United Kingdom, else 0
- days_since_last_order (integer): days since their last order
- num_orders (integer): total number of orders ever placed
- total_spent (decimal): total spent ever, in GBP
- avg_order_value (decimal): average spend per order, in GBP
- days_as_customer (integer): days since their first order
- orders_last_90_days (integer): orders in the last 90 days
- spent_last_90_days (decimal): spend in the last 90 days, in GBP
- different_products (integer): number of different products bought
- cancelled_orders (integer): number of cancelled orders
- spent_last_12_months (decimal): spend in the last 12 months, in GBP
- cancel_rate (decimal): cancelled orders divided by orders
- churn_probability (decimal): model's chance the customer will stop buying, from 0 to 1
- revenue_at_risk (decimal): churn_probability x spent_last_12_months, in GBP
- risk_group (text): exactly one of 'High', 'Medium', 'Low'
- suggested_action (text): exactly one of 'Win-back contact', 'Second order offer',
  'Cross-sell new products', 'No action needed'
"""

SQL_RULES = """
You are a data analyst who writes DuckDB SQL.
Write ONE SQL query that answers the user's question using the table below.

Rules:
- Only use the customer_risk table and the columns listed.
- Only write SELECT queries. Never change the data.
- Round money to 2 decimal places and percentages to 1 decimal place.
- Round probabilities to 3 decimal places. They are between 0 and 1, not percentages.
- If the question asks for a list of customers, add LIMIT 20.
- Reply with ONLY the SQL query. No explanation.
"""


# ---- 3. Small helper functions ----

def ask_model(prompt):
    """Send a prompt to the AI model and return its reply as text."""
    response = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}],
                           options={"temperature": 0})
    return response["message"]["content"]


def clean_sql(text):
    """Remove the ```sql ... ``` marks the model likes to add."""
    text = text.strip()
    if "```" in text:
        # Keep only what's between the first pair of ``` marks
        text = text.split("```")[1]
        # Drop the word "sql" if it's at the start
        if text.lower().startswith("sql"):
            text = text[3:]
    # Remove a trailing semicolon, DuckDB doesn't need it
    return text.strip().rstrip(";").strip()


def is_safe(sql):
    """Only allow read-only queries. Block anything that could change data."""
    upper = sql.upper()
    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        return False
    blocked = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "ATTACH", "COPY", "PRAGMA", ";"]
    for word in blocked:
        if word in upper:
            return False
    return True


def write_sql(question):
    """Ask the AI to write SQL for a question."""
    prompt = SQL_RULES + "\n" + TABLE_DESCRIPTION + "\nQuestion: " + question
    return clean_sql(ask_model(prompt))


def fix_sql(question, bad_sql, error):
    """If the SQL failed, show the AI the error and ask it to fix it."""
    prompt = (SQL_RULES + "\n" + TABLE_DESCRIPTION +
              "\nQuestion: " + question +
              "\n\nYour previous SQL was:\n" + bad_sql +
              "\n\nIt gave this error:\n" + str(error) +
              "\n\nWrite a corrected SQL query.")
    return clean_sql(ask_model(prompt))


def explain(question, result):
    """Ask the AI to turn the result table into a short plain-English answer."""
    prompt = (
        "You are a data analyst explaining results to a manager.\n"
        "Answer the question in one or two plain sentences, using ONLY the numbers "
        "in the result below. Do not make up any numbers. Money is in GBP (£).\n\n"
        "Question: " + question + "\n\n"
        "Result:\n" + result.head(20).to_string(index=False)
    )
    return ask_model(prompt).strip()


def answer(question, explain_result=True):
    """The full flow: question -> SQL -> result -> plain-English answer.
    Returns a dictionary so we can reuse it later when testing the assistant.
    Set explain_result=False to skip the plain-English step (faster for testing)."""
    sql = write_sql(question)

    if not is_safe(sql):
        return {"sql": sql, "result": None, "answer": "Sorry, I can only run read-only questions."}

    try:
        result = con.execute(sql).df()
    except Exception as error:
        # Give the AI one chance to fix its own mistake
        sql = fix_sql(question, sql, error)
        if not is_safe(sql):
            return {"sql": sql, "result": None, "answer": "Sorry, I can only run read-only questions."}
        try:
            result = con.execute(sql).df()
        except Exception as error2:
            return {"sql": sql, "result": None, "answer": "Sorry, I couldn't answer that. Error: " + str(error2)}

    if len(result) == 0:
        return {"sql": sql, "result": result, "answer": "The query returned no results."}

    if not explain_result:
        return {"sql": sql, "result": result, "answer": ""}

    return {"sql": sql, "result": result, "answer": explain(question, result)}


# ---- 4. The chat loop ----
# Only runs when you start this file directly (not when another script imports it)
if __name__ == "__main__":
    print("AI analyst assistant. Ask a question about the customers, or type 'quit'.")
    print("Example: How much revenue is at risk in Germany?\n")

    while True:
        question = input("Your question: ").strip()
        if question.lower() in ["quit", "exit", "q"]:
            break
        if question == "":
            continue

        print("Thinking...")
        reply = answer(question)

        print("\nSQL used:")
        print(reply["sql"])
        if reply["result"] is not None and len(reply["result"]) > 0:
            print("\nResult:")
            print(reply["result"].head(20).to_string(index=False))
        print("\nAnswer:", reply["answer"])
        print("\n" + "-" * 60 + "\n")