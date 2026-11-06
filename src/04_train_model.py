# 04_train_model.py
# Train churn models and compare them.
#
# We try two models:
#   1. Logistic regression - simple, easy to explain
#   2. Random forest      - more powerful, can find non-linear patterns
# and compare both against a "dumb" baseline.

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score


# ---- 1. Load the customer table we built in SQL ----
df = pd.read_csv("data/customer_features.csv")
print("Customers:", len(df))


# ---- 2. One extra feature ----
# Remember the cancellation finding: raw counts were misleading because
# active customers order more. So we use cancellations PER ORDER instead.
df["cancel_rate"] = df["cancelled_orders"] / df["num_orders"]


# ---- 3. Pick the inputs (X) and the answer we want to predict (y) ----
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
X = df[features]
y = df["churned"]


# ---- 4. Split into training and test data ----
# The model learns from 80% of customers, and we test it on the other 20%
# that it has never seen. stratify=y keeps the same churn rate in both parts.
# random_state=42 means we get the same split every time we run this.
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print("Training customers:", len(X_train))
print("Test customers:", len(X_test))


# ---- 5. Baseline: what if we just guessed "nobody churns"? ----
# Any real model has to beat this, otherwise it's useless.
baseline_accuracy = (y_test == 0).mean()
print("\nBaseline accuracy (guess nobody churns):", round(baseline_accuracy, 3))


# ---- 6. Small helper to print the results of a model ----
def show_results(model_name, y_true, predictions, probabilities):
    print("\n=====", model_name, "=====")
    print("Accuracy :", round(accuracy_score(y_true, predictions), 3))
    print("Precision:", round(precision_score(y_true, predictions), 3))
    print("Recall   :", round(recall_score(y_true, predictions), 3))
    print("ROC AUC  :", round(roc_auc_score(y_true, probabilities), 3))


# ---- 7. Model 1: Logistic regression ----
# Logistic regression works best when all features are on a similar scale
# (otherwise total_spent in the thousands drowns out is_uk which is 0 or 1).
# We fit the scaler on the TRAINING data only, then apply it to the test data.
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

log_model = LogisticRegression(max_iter=1000)
log_model.fit(X_train_scaled, y_train)

log_pred = log_model.predict(X_test_scaled)
log_prob = log_model.predict_proba(X_test_scaled)[:, 1]   # chance of churning
show_results("Logistic regression", y_test, log_pred, log_prob)


# ---- 8. Model 2: Random forest ----
# Random forests don't need scaling, so we use the original numbers.
forest_model = RandomForestClassifier(n_estimators=300, random_state=42)
forest_model.fit(X_train, y_train)

forest_pred = forest_model.predict(X_test)
forest_prob = forest_model.predict_proba(X_test)[:, 1]
show_results("Random forest", y_test, forest_pred, forest_prob)


# ---- 9. Which features does the random forest rely on most? ----
importance = pd.DataFrame({
    "feature": features,
    "importance": forest_model.feature_importances_
})
importance = importance.sort_values("importance", ascending=False)

print("\n===== Most important features (random forest) =====")
print(importance.to_string(index=False))