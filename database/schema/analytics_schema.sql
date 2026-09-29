-- Regions (Indian states/zones)
CREATE TABLE IF NOT EXISTS regions (
    region_id SERIAL PRIMARY KEY,
    region_name VARCHAR(100) NOT NULL,
    zone VARCHAR(50) NOT NULL,  -- North, South, East, West
    country VARCHAR(100) DEFAULT 'India'
);

-- Categories
CREATE TABLE IF NOT EXISTS categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    description TEXT
);

-- Customers
CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(200) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    city VARCHAR(100),
    state VARCHAR(100),
    region_id INTEGER REFERENCES regions(region_id),
    segment VARCHAR(50) CHECK (segment IN ('Enterprise', 'SMB', 'Consumer')),
    signup_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Employees
CREATE TABLE IF NOT EXISTS employees (
    employee_id SERIAL PRIMARY KEY,
    employee_name VARCHAR(200) NOT NULL,
    department VARCHAR(100),
    role VARCHAR(100),
    region_id INTEGER REFERENCES regions(region_id),
    hire_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Products
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(300) NOT NULL,
    category_id INTEGER REFERENCES categories(category_id),
    price DECIMAL(12, 2) NOT NULL,
    cost DECIMAL(12, 2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_date DATE NOT NULL
);

-- Orders
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    order_date DATE NOT NULL,
    status VARCHAR(50) CHECK (status IN ('completed', 'pending', 'cancelled', 'returned', 'processing')) DEFAULT 'pending',
    total_amount DECIMAL(12, 2) NOT NULL,
    discount_amount DECIMAL(12, 2) DEFAULT 0,
    payment_method VARCHAR(50) CHECK (payment_method IN ('credit_card', 'debit_card', 'upi', 'net_banking', 'cod', 'wallet')),
    employee_id INTEGER REFERENCES employees(employee_id)
);

-- Order items
CREATE TABLE IF NOT EXISTS order_items (
    item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(12, 2) NOT NULL,
    total_price DECIMAL(12, 2) NOT NULL
);

-- Payments
CREATE TABLE IF NOT EXISTS payments (
    payment_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    amount DECIMAL(12, 2) NOT NULL,
    payment_status VARCHAR(50) CHECK (payment_status IN ('completed', 'pending', 'failed', 'refunded')) DEFAULT 'pending',
    payment_date DATE NOT NULL,
    payment_method VARCHAR(50)
);

-- Indexes for analytics queries
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_customers_region_id ON customers(region_id);
CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments(order_id);
