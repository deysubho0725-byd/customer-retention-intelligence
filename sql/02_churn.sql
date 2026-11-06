-- 02_churn.sql
-- Define which customers churned.
--
-- Our rule:
--   1. Pick a cutoff date, 180 days before the last date in the data.
--   2. Look at every customer who bought at least once BEFORE the cutoff.
--   3. If they bought nothing in the 180 days AFTER the cutoff, they churned.

-- Step 1: work out the cutoff date
CREATE OR REPLACE VIEW churn_dates AS
SELECT
    MAX(order_date)                       AS last_date_in_data,
    MAX(order_date) - INTERVAL 180 DAY    AS cutoff_date
FROM orders;


-- Q3: What are the key dates?
SELECT * FROM churn_dates;


-- Step 2: what each customer did BEFORE the cutoff
-- (later, the model will only be allowed to learn from this part)
CREATE OR REPLACE VIEW before_cutoff AS
SELECT
    customer_id,
    MAX(order_date)    AS last_order_date,
    COUNT(*)           AS num_orders,
    SUM(order_value)   AS total_spent
FROM orders
WHERE order_date <= (SELECT cutoff_date FROM churn_dates)
GROUP BY customer_id;


-- Step 3: customers who bought anything AFTER the cutoff
CREATE OR REPLACE VIEW after_cutoff AS
SELECT DISTINCT customer_id
FROM orders
WHERE order_date > (SELECT cutoff_date FROM churn_dates);


-- Step 4: put them together.
-- LEFT JOIN keeps every "before" customer. If there's no match in
-- after_cutoff, that customer never came back, so churned = 1.
CREATE OR REPLACE VIEW churn_labels AS
SELECT
    b.*,
    DATE_DIFF('day', b.last_order_date, (SELECT cutoff_date FROM churn_dates)) AS days_since_last_order,
    CASE WHEN a.customer_id IS NULL THEN 1 ELSE 0 END AS churned
FROM before_cutoff b
LEFT JOIN after_cutoff a
    ON b.customer_id = a.customer_id;


-- Q4: How many customers churned?
SELECT
    COUNT(*)                         AS customers,
    SUM(churned)                     AS churned,
    ROUND(100.0 * AVG(churned), 1)   AS churn_rate_pct
FROM churn_labels;


-- Q5: Churn rate by how long since their last order (at the cutoff)
SELECT
    CASE
        WHEN days_since_last_order <= 30  THEN '1. 0-30 days'
        WHEN days_since_last_order <= 90  THEN '2. 31-90 days'
        WHEN days_since_last_order <= 180 THEN '3. 91-180 days'
        WHEN days_since_last_order <= 365 THEN '4. 181-365 days'
        ELSE '5. Over a year'
    END                              AS last_order_group,
    COUNT(*)                         AS customers,
    ROUND(100.0 * AVG(churned), 1)   AS churn_rate_pct
FROM churn_labels
GROUP BY last_order_group
ORDER BY last_order_group;