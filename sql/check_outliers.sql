-- check_outliers.sql
-- The top customers by revenue at risk look suspicious.
-- Were their big orders cancelled?

-- Q1: Biggest purchase lines for the top 4 suspicious customers
SELECT
    customer_id,
    invoice,
    invoice_date,
    stock_code,
    description,
    quantity,
    ROUND(revenue, 2) AS revenue
FROM transactions
WHERE customer_id IN (16446, 12346, 15749, 15098)
ORDER BY revenue DESC
LIMIT 10;


-- Q2: Their cancellations (biggest first)
SELECT
    customer_id,
    invoice,
    invoice_date,
    stock_code,
    quantity
FROM cancellations
WHERE customer_id IN (16446, 12346, 15749, 15098)
ORDER BY quantity ASC
LIMIT 10;