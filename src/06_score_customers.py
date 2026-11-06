# 06_score_customers.py
# Score every current customer for churn risk and work out revenue at risk.
#
# 1. Train the logistic regression on the historical snapshot
#    (customer_features.csv, where we KNOW who churned).
# 2. Use it to predict churn for current customers
#    (current_customers.csv, where we DON'T know yet).
# 3. Revenue at risk = chance of churning x what they spent in the last 12 months.

import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression


# Same features as Step 12
features = [
    "days_since_last_order",
    "num_orders",
    "total_spent",
    "avg_order_value",
    "days_as_customer",
    "orders_last_90_days",
    "spent_last_90_days",
    "different_products",
    "cancel_rate",
    "is_uk",
]


# ---- 1. Train the model on the historical data ----
# We already tested it on unseen customers in Step 12 (ROC AUC 0.786),
# so now we train on ALL historical customers to give it the most to learn from.
history = pd.read_csv("data/customer_features.csv")
history["cancel_rate"] = history["cancelled_orders"] / history["num_orders"]

scaler = StandardScaler()
X_history = scaler.fit_transform(history[features])

model = LogisticRegression(max_iter=1000)
model.fit(X_history, history["churned"])


# ---- 2. Score the current customers ----
current = pd.read_csv("data/current_customers.csv")
current["cancel_rate"] = current["cancelled_orders"] / current["num_orders"]

# Use the SAME scaler from the training data (don't fit a new one)
X_current = scaler.transform(current[features])

# Chance of churning, between 0 and 1
current["churn_probability"] = model.predict_proba(X_current)[:, 1].round(3)


# ---- 3. Revenue at risk ----
# Example: a customer who spent 1,000 last year with a 0.6 chance of leaving
# puts 600 of expected revenue at risk.
current["revenue_at_risk"] = (current["churn_probability"] * current["spent_last_12_months"]).round(2)


# ---- 4. Risk groups, so the business can act on them ----
def risk_group(probability):
    if probability >= 0.6:
        return "High"
    elif probability >= 0.3:
        return "Medium"
    else:
        return "Low"

current["risk_group"] = current["churn_probability"].apply(risk_group)


# ---- 5. Suggested action, based on our churn driver findings (Step 14) ----
def suggested_action(row):
    if row["risk_group"] == "Low":
        return "No action needed"
    elif row["num_orders"] == 1:
        return "Second order offer"        # Finding 1: the second order is key
    elif row["orders_last_90_days"] == 0:
        return "Win-back contact"          # Finding 2: 90 days of silence
    else:
        return "Cross-sell new products"   # Finding 3: variety keeps customers

current["suggested_action"] = current.apply(suggested_action, axis=1)


# ---- 6. Summary by risk group ----
summary = current.groupby("risk_group").agg(
    customers=("customer_id", "count"),
    revenue_last_12_months=("spent_last_12_months", "sum"),
    revenue_at_risk=("revenue_at_risk", "sum"),
).round(0)

# Put the groups in a sensible order
summary = summary.reindex(["High", "Medium", "Low"])

print("===== Customers by risk group =====")
print(summary)
print("\nTotal revenue at risk (GBP):", round(current["revenue_at_risk"].sum()))
print("Share of last year's revenue at risk:",
      round(100 * current["revenue_at_risk"].sum() / current["spent_last_12_months"].sum(), 1), "%")


# ---- 7. Suggested actions for High and Medium risk customers ----
at_risk = current[current["risk_group"] != "Low"]

actions = at_risk.groupby("suggested_action").agg(
    customers=("customer_id", "count"),
    revenue_at_risk=("revenue_at_risk", "sum"),
).round(0).sort_values("revenue_at_risk", ascending=False)

print("\n===== Suggested actions (High and Medium risk) =====")
print(actions)


# ---- 8. Top 10 customers to contact first ----
top10 = current.sort_values("revenue_at_risk", ascending=False).head(10)

print("\n===== Top 10 customers by revenue at risk =====")
print(top10[[
    "customer_id", "country", "churn_probability",
    "spent_last_12_months", "revenue_at_risk", "suggested_action"
]].to_string(index=False))


# ---- 9. Save for Power BI ----
current.to_csv("data/customer_risk_scores.csv", index=False)
print("\nSaved data/customer_risk_scores.csv")