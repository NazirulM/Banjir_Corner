CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(50) PRIMARY KEY,
    dine_option VARCHAR(20),
    submitted_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20),
    payment_status VARCHAR(20),
    payment_method VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS order_items (
    item_id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) REFERENCES orders(order_id),
    item VARCHAR(50),
    quantity INTEGER,
    price DECIMAL,
    subtotal DECIMAL
);

-- Add a new column to order_items table
ALTER TABLE order_items ADD COLUMN remarks TEXT;

-- Delete a column called remarks from orders table
ALTER TABLE orders DROP COLUMN remarks;

SELECT * FROM orders;
SELECT * FROM order_items;

-- delete all records from orders and order_items tables
TRUNCATE TABLE orders, order_items;