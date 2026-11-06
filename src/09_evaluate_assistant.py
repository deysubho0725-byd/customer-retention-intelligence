# 09_evaluate_assistant.py
# How accurate is the AI assistant?
#
# We ask it 30 business questions where WE already know the right answer,
# because we wrote the correct SQL ourselves. Then we compare its result
# with the correct result and count how many it got right.
#
# Run it with:  python src/09_evaluate_assistant.py
# (Takes a few minutes, the AI answers 30 questions one by one.)

import math
import pandas as pd
from ai_assistant import answer, con


# ---- 1. The test questions and the correct SQL for each ----
TESTS = [
    # Simple totals
    ("How much revenue is at risk in total?",
     "SELECT SUM(revenue_at_risk) FROM customer_risk"),
    ("How many current customers are there?",
     "SELECT COUNT(*) FROM customer_risk"),
    ("What is the total spend of all customers in the last 12 months?",
     "SELECT SUM(spent_last_12_months) FROM customer_risk"),
    ("What percentage of last 12 months revenue is at risk?",
     "SELECT 100 * SUM(revenue_at_risk) / SUM(spent_last_12_months) FROM customer_risk"),
    ("What is the average churn probability across all customers?",
     "SELECT AVG(churn_probability) FROM customer_risk"),

    # Filters
    ("How much revenue is at risk in Ireland?",
     "SELECT SUM(revenue_at_risk) FROM customer_risk WHERE country = 'EIRE'"),
    ("How much revenue is at risk in Germany?",
     "SELECT SUM(revenue_at_risk) FROM customer_risk WHERE country = 'Germany'"),
    ("How many customers are in France?",
     "SELECT COUNT(*) FROM customer_risk WHERE country = 'France'"),
    ("How many customers have only placed one order?",
     "SELECT COUNT(*) FROM customer_risk WHERE num_orders = 1"),
    ("How much revenue is at risk from customers who have only ordered once?",
     "SELECT SUM(revenue_at_risk) FROM customer_risk WHERE num_orders = 1"),
    ("How many customers have not ordered in more than 90 days?",
     "SELECT COUNT(*) FROM customer_risk WHERE days_since_last_order > 90"),
    ("How many customers have a churn probability above 0.5?",
     "SELECT COUNT(*) FROM customer_risk WHERE churn_probability > 0.5"),
    ("How many high risk customers are in the UK?",
     "SELECT COUNT(*) FROM customer_risk WHERE risk_group = 'High' AND country = 'United Kingdom'"),
    ("How many customers have cancelled at least one order?",
     "SELECT COUNT(*) FROM customer_risk WHERE cancelled_orders > 0"),
    ("How many customers need a win-back contact?",
     "SELECT COUNT(*) FROM customer_risk WHERE suggested_action = 'Win-back contact'"),
    ("How much revenue is at risk for customers who should get a second order offer?",
     "SELECT SUM(revenue_at_risk) FROM customer_risk WHERE suggested_action = 'Second order offer'"),
    ("What is the average order value of high risk customers?",
     "SELECT AVG(avg_order_value) FROM customer_risk WHERE risk_group = 'High'"),
    ("What is the average churn probability of high risk customers?",
     "SELECT AVG(churn_probability) FROM customer_risk WHERE risk_group = 'High'"),

    # Group by
    ("How many customers are in each risk group?",
     "SELECT risk_group, COUNT(*) FROM customer_risk GROUP BY risk_group"),
    ("How much revenue is at risk in each risk group?",
     "SELECT risk_group, SUM(revenue_at_risk) FROM customer_risk GROUP BY risk_group"),
    ("How much revenue is at risk for each suggested action?",
     "SELECT suggested_action, SUM(revenue_at_risk) FROM customer_risk GROUP BY suggested_action"),
    ("What is the average number of days since last order for each risk group?",
     "SELECT risk_group, AVG(days_since_last_order) FROM customer_risk GROUP BY risk_group"),
    ("How much revenue is at risk from UK customers compared with customers outside the UK?",
     "SELECT SUM(revenue_at_risk) FROM customer_risk GROUP BY is_uk"),

    # Rankings
    ("Who are the top 5 customers by revenue at risk?",
     "SELECT customer_id FROM customer_risk ORDER BY revenue_at_risk DESC LIMIT 5"),
    ("Who are the top 5 customers by spend in the last 12 months?",
     "SELECT customer_id FROM customer_risk ORDER BY spent_last_12_months DESC LIMIT 5"),
    ("Which customer spent the most in the last 12 months?",
     "SELECT customer_id FROM customer_risk ORDER BY spent_last_12_months DESC LIMIT 1"),
    ("Which country outside the UK has the most revenue at risk?",
     "SELECT country FROM customer_risk WHERE country <> 'United Kingdom' GROUP BY country ORDER BY SUM(revenue_at_risk) DESC LIMIT 1"),
    ("What are the top 3 countries by number of customers?",
     "SELECT country FROM customer_risk GROUP BY country ORDER BY COUNT(*) DESC LIMIT 3"),

    # Other
    ("How many different countries do customers come from?",
     "SELECT COUNT(DISTINCT country) FROM customer_risk"),
    ("What is the median spend in the last 12 months?",
     "SELECT MEDIAN(spent_last_12_months) FROM customer_risk"),
]


# ---- 2. How we decide if the AI's answer is right ----
def values_in(df):
    """Turn every cell of a result table into a flat list of values."""
    out = []
    for value in df.to_numpy().flatten():
        if isinstance(value, str):
            out.append(value.strip().lower())
        elif pd.notna(value):
            out.append(float(value))
    return out


def same_value(correct, ai):
    """Do two values match? Text must match exactly (ignoring case).
    Whole numbers (counts, customer IDs) must match exactly.
    Other numbers can differ by up to 1%, so rounding doesn't count as wrong."""
    if isinstance(correct, str) or isinstance(ai, str):
        return correct == ai
    if correct.is_integer() and ai.is_integer():
        return correct == ai
    return math.isclose(correct, ai, rel_tol=0.01, abs_tol=0.01)


def is_correct(correct_df, ai_df):
    """The AI is right if every value in the correct answer appears in its result.
    Extra columns are fine (like adding a name next to a number)."""
    if ai_df is None or len(ai_df) == 0:
        return False
    ai_values = values_in(ai_df)
    for correct in values_in(correct_df):
        if not any(same_value(correct, ai) for ai in ai_values):
            return False
    return True


# ---- 3. Run every test ----
results = []

for number, (question, correct_sql) in enumerate(TESTS, start=1):
    correct_df = con.execute(correct_sql).df()

    # explain_result=False skips the plain-English step, which makes testing faster
    reply = answer(question, explain_result=False)
    passed = is_correct(correct_df, reply["result"])

    print(f"{number:2}. {'PASS' if passed else 'FAIL'}  {question}")
    results.append({"question": question, "passed": passed,
                    "ai_sql": reply["sql"], "correct_sql": correct_sql})


# ---- 4. Final score ----
results = pd.DataFrame(results)
score = results["passed"].sum()
print(f"\nScore: {score} out of {len(results)} ({100 * score / len(results):.0f}%)")

# Save everything so we can look at the failures properly
results.to_csv("data/assistant_evaluation.csv", index=False)
print("Saved details to data/assistant_evaluation.csv")