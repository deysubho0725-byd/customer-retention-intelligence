-- 03_features.sql
-- Build one row per customer with everything the model will learn from.
--
-- Rules:
--   * Only use data from BEFORE the cutoff date (no peeking at the future).
--   * Only keep customers who ordered in the 12 months before the cutoff.
--     Customers gone for over a year are easy to predict and would make
--     the model look better than it really is.

CREATE OR REPLACE VIEW customer_features AS
WITH

-- When did each customer first buy?
first_order AS (
    SELECT customer_id, MIN(order_date) AS first_order_date
    FROM orders
    WHERE order_date <= (SELECT cutoff_date FROM churn_dates)
    GROUP BY customer_id
),

-- What did they do in the last 90 days before the cutoff?
last_90_days AS (
    SELECT
        customer_id,
        COUNT(*)          AS orders_last_90_days,
        SUM(order_value)  AS spent_last_90_days
    FROM orders
    WHERE order_date <= (SELECT cutoff_date FROM churn_dates)
      AND order_date >  (SELECT cutoff_date FROM churn_dates) - INTERVAL 90 DAY
    GROUP BY customer_id
),

-- How many different products have they bought?
products AS (
    SELECT customer_id, COUNT(DISTINCT stock_code) AS different_products
    FROM transactions
    WHERE invoice_date <= (SELECT cutoff_date FROM churn_dates)
    GROUP BY customer_id
),

-- How many orders did they cancel?
cancels AS (
    SELECT customer_id, COUNT(DISTINCT invoice) AS cancelled_orders
    FROM cancellations
    WHERE invoice_date <= (SELECT cutoff_date FROM churn_dates)
    GROUP BY customer_id
),

-- Which country do they usually order from? (MODE = most common value)
country AS (
    SELECT customer_id, MODE(country) AS country
    FROM orders
    WHERE order_date <= (SELECT cutoff_date FROM churn_dates)
    GROUP BY customer_id
)

SELECT
    c.customer_id,
    co.country,
    CASE WHEN co.country = 'United Kingdom' THEN 1 ELSE 0 END  AS is_uk,

    -- How recently, how often, how much (the classic "RFM")
    c.days_since_last_order,
    c.num_orders,
    ROUND(c.total_spent, 2)                                     AS total_spent,
    ROUND(c.total_spent / c.num_orders, 2)                      AS avg_order_value,

    -- How long they've been a customer
    DATE_DIFF('day', f.first_order_date, (SELECT cutoff_date FROM churn_dates)) AS days_as_customer,

    -- Recent activity (0 if they did nothing in the last 90 days)
    COALESCE(l.orders_last_90_days, 0)                          AS orders_last_90_days,
    ROUND(COALESCE(l.spent_last_90_days, 0), 2)                 AS spent_last_90_days,

    -- Variety and returns
    p.different_products,
    COALESCE(x.cancelled_orders, 0)                             AS cancelled_orders,

    -- What we want to predict
    c.churned

FROM churn_labels c
LEFT JOIN first_order   f  ON c.customer_id = f.customer_id
LEFT JOIN last_90_days  l  ON c.customer_id = l.customer_id
LEFT JOIN products      p  ON c.customer_id = p.customer_id
LEFT JOIN cancels       x  ON c.customer_id = x.customer_id
LEFT JOIN country       co ON c.customer_id = co.customer_id
WHERE c.days_since_last_order <= 365;


-- Q6: How many customers are left, and what is their churn rate?
SELECT
    COUNT(*)                         AS customers,
    SUM(churned)                     AS churned,
    ROUND(100.0 * AVG(churned), 1)   AS churn_rate_pct
FROM customer_features;


-- Q7: How do customers who churned differ from those who stayed?
SELECT
    CASE WHEN churned = 1 THEN 'Churned' ELSE 'Stayed' END  AS customer_group,
    COUNT(*)                                     AS customers,
    ROUND(AVG(days_since_last_order))            AS avg_days_since_last_order,
    ROUND(AVG(num_orders), 1)                    AS avg_orders,
    ROUND(AVG(total_spent))                      AS avg_total_spent,
    ROUND(AVG(avg_order_value))                  AS avg_order_value,
    ROUND(AVG(days_as_customer))                 AS avg_days_as_customer,
    ROUND(AVG(orders_last_90_days), 1)           AS avg_orders_last_90_days,
    ROUND(AVG(cancelled_orders), 1)              AS avg_cancelled_orders
FROM customer_features
GROUP BY customer_group;


-- Save the table as a CSV, ready for the model in Python
COPY (SELECT * FROM customer_features)
TO 'data/customer_features.csv' (HEADER);