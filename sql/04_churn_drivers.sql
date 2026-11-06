-- 04_churn_drivers.sql
-- What drives churn? We split customers into groups for each factor
-- and compare churn rates. If the churn rate changes a lot between
-- groups, that factor matters.
--
-- NTILE(4) splits customers into 4 equal-sized groups (quartiles),
-- from lowest (1) to highest (4).


-- Q8: Number of orders before the cutoff
SELECT
    CASE
        WHEN num_orders = 1  THEN '1. One order'
        WHEN num_orders <= 3 THEN '2. 2-3 orders'
        WHEN num_orders <= 9 THEN '3. 4-9 orders'
        ELSE '4. 10+ orders'
    END                              AS order_group,
    COUNT(*)                         AS customers,
    ROUND(100.0 * AVG(churned), 1)   AS churn_rate_pct
FROM customer_features
GROUP BY order_group
ORDER BY order_group;


-- Q9: Orders in the last 90 days before the cutoff
SELECT
    CASE
        WHEN orders_last_90_days = 0 THEN '1. None'
        WHEN orders_last_90_days = 1 THEN '2. One'
        WHEN orders_last_90_days = 2 THEN '3. Two'
        ELSE '4. Three or more'
    END                              AS recent_orders,
    COUNT(*)                         AS customers,
    ROUND(100.0 * AVG(churned), 1)   AS churn_rate_pct
FROM customer_features
GROUP BY recent_orders
ORDER BY recent_orders;


-- Q10: Average order value (quartiles)
SELECT
    quartile,
    COUNT(*)                         AS customers,
    ROUND(MIN(avg_order_value))      AS from_gbp,
    ROUND(MAX(avg_order_value))      AS to_gbp,
    ROUND(100.0 * AVG(churned), 1)   AS churn_rate_pct
FROM (
    SELECT *, NTILE(4) OVER (ORDER BY avg_order_value) AS quartile
    FROM customer_features
)
GROUP BY quartile
ORDER BY quartile;


-- Q11: How long they've been a customer (quartiles)
SELECT
    quartile,
    COUNT(*)                         AS customers,
    MIN(days_as_customer)            AS from_days,
    MAX(days_as_customer)            AS to_days,
    ROUND(100.0 * AVG(churned), 1)   AS churn_rate_pct
FROM (
    SELECT *, NTILE(4) OVER (ORDER BY days_as_customer) AS quartile
    FROM customer_features
)
GROUP BY quartile
ORDER BY quartile;


-- Q12: Product variety (quartiles)
SELECT
    quartile,
    COUNT(*)                         AS customers,
    MIN(different_products)          AS from_products,
    MAX(different_products)          AS to_products,
    ROUND(100.0 * AVG(churned), 1)   AS churn_rate_pct
FROM (
    SELECT *, NTILE(4) OVER (ORDER BY different_products) AS quartile
    FROM customer_features
)
GROUP BY quartile
ORDER BY quartile;


-- Q13: Do customers who cancel churn more? (using cancellations PER ORDER)
SELECT
    CASE
        WHEN cancelled_orders = 0                      THEN '1. Never cancelled'
        WHEN cancelled_orders * 1.0 / num_orders < 0.2 THEN '2. Under 20% of orders'
        ELSE '3. 20% of orders or more'
    END                              AS cancel_group,
    COUNT(*)                         AS customers,
    ROUND(100.0 * AVG(churned), 1)   AS churn_rate_pct
FROM customer_features
GROUP BY cancel_group
ORDER BY cancel_group;


-- Q14: UK vs international customers
SELECT
    CASE WHEN is_uk = 1 THEN 'UK' ELSE 'International' END  AS region,
    COUNT(*)                         AS customers,
    ROUND(100.0 * AVG(churned), 1)   AS churn_rate_pct
FROM customer_features
GROUP BY region;