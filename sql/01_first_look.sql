-- 01_first_look.sql
-- First business questions about the shop.
-- Prices are in GBP.

-- An "orders" view: one row per invoice instead of one row per product line.
-- A view is like a saved query you can use as if it were a table.
CREATE OR REPLACE VIEW orders AS
SELECT
    invoice,
    customer_id,
    country,
    MIN(invoice_date)  AS order_date,   -- all lines in an invoice share the same date
    COUNT(*)           AS products,     -- how many different products in the order
    SUM(revenue)       AS order_value   -- total spent on this order
FROM transactions
GROUP BY invoice, customer_id, country;


-- Q1: How do revenue, customers and orders change month by month?
SELECT
    DATE_TRUNC('month', order_date)  AS month,
    ROUND(SUM(order_value))          AS revenue,
    COUNT(DISTINCT customer_id)      AS customers,
    COUNT(*)                         AS orders
FROM orders
GROUP BY month
ORDER BY month;


-- Q2: Which 10 countries bring in the most revenue?
SELECT
    country,
    ROUND(SUM(order_value))       AS revenue,
    COUNT(DISTINCT customer_id)   AS customers
FROM orders
GROUP BY country
ORDER BY revenue DESC
LIMIT 10;