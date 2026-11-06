-- 05_current_customers.sql
-- Build the same customer features as 03_features.sql, but as of the
-- LAST day in the data instead of the cutoff date.
--
-- These are the customers the business cares about right now.
-- In Part B, the model will score each of them for churn risk.
--
-- We keep customers who ordered in the last 12 months (same rule as before).

CREATE OR REPLACE VIEW current_customers AS
WITH

-- The basics for every customer, using ALL their history
basics AS (
    SELECT
        customer_id,
        MIN(order_date)    AS first_order_date,
        MAX(order_date)    AS last_order_date,
        COUNT(*)           AS num_orders,
        SUM(order_value)   AS total_spent
    FROM orders
    GROUP BY customer_id
),

-- Activity in the last 90 days of the data
last_90_days AS (
    SELECT
        customer_id,
        COUNT(*)          AS orders_last_90_days,
        SUM(order_value)  AS spent_last_90_days
    FROM orders
    WHERE order_date > (SELECT last_date_in_data FROM churn_dates) - INTERVAL 90 DAY
    GROUP BY customer_id
),

-- Spend in the last 12 months: this is the yearly revenue we could lose
last_12_months AS (
    SELECT customer_id, SUM(order_value) AS spent_last_12_months
    FROM orders
    WHERE order_date > (SELECT last_date_in_data FROM churn_dates) - INTERVAL 365 DAY
    GROUP BY customer_id
),

-- How many different products they've bought
products AS (
    SELECT customer_id, COUNT(DISTINCT stock_code) AS different_products
    FROM transactions
    GROUP BY customer_id
),

-- How many orders they've cancelled
cancels AS (
    SELECT customer_id, COUNT(DISTINCT invoice) AS cancelled_orders
    FROM cancellations
    GROUP BY customer_id
),

-- Their most common country
country AS (
    SELECT customer_id, MODE(country) AS country
    FROM orders
    GROUP BY customer_id
)

SELECT
    b.customer_id,
    co.country,
    CASE WHEN co.country = 'United Kingdom' THEN 1 ELSE 0 END  AS is_uk,
    DATE_DIFF('day', b.last_order_date, (SELECT last_date_in_data FROM churn_dates))  AS days_since_last_order,
    b.num_orders,
    ROUND(b.total_spent, 2)                                     AS total_spent,
    ROUND(b.total_spent / b.num_orders, 2)                      AS avg_order_value,
    DATE_DIFF('day', b.first_order_date, (SELECT last_date_in_data FROM churn_dates)) AS days_as_customer,
    COALESCE(l.orders_last_90_days, 0)                          AS orders_last_90_days,
    ROUND(COALESCE(l.spent_last_90_days, 0), 2)                 AS spent_last_90_days,
    p.different_products,
    COALESCE(x.cancelled_orders, 0)                             AS cancelled_orders,
    ROUND(COALESCE(y.spent_last_12_months, 0), 2)               AS spent_last_12_months

FROM basics b
LEFT JOIN last_90_days    l  ON b.customer_id = l.customer_id
LEFT JOIN last_12_months  y  ON b.customer_id = y.customer_id
LEFT JOIN products        p  ON b.customer_id = p.customer_id
LEFT JOIN cancels         x  ON b.customer_id = x.customer_id
LEFT JOIN country         co ON b.customer_id = co.customer_id
WHERE DATE_DIFF('day', b.last_order_date, (SELECT last_date_in_data FROM churn_dates)) <= 365;


-- Q15: How many current customers, and how much did they spend in the last year?
SELECT
    COUNT(*)                            AS current_customers,
    ROUND(SUM(spent_last_12_months))    AS revenue_last_12_months_gbp,
    ROUND(AVG(days_since_last_order))   AS avg_days_since_last_order
FROM current_customers;


-- Save as a CSV for scoring in Python
COPY (SELECT * FROM current_customers)
TO 'data/current_customers.csv' (HEADER);