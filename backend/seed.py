import asyncio
import os
import sys
import random
from pathlib import Path
from datetime import datetime, timedelta

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import asyncpg
from app.config import settings
from app.database import clean_db_url

# Indian Demographics & Geographies
CITIES_STATES = [
    ("Mumbai", "Maharashtra", "West", "400001"),
    ("Pune", "Maharashtra", "West", "411001"),
    ("Nagpur", "Maharashtra", "West", "440001"),
    ("Bengaluru", "Karnataka", "South", "560001"),
    ("Mysuru", "Karnataka", "South", "570001"),
    ("Hyderabad", "Telangana", "South", "500001"),
    ("Chennai", "Tamil Nadu", "South", "600001"),
    ("Coimbatore", "Tamil Nadu", "South", "641001"),
    ("Kochi", "Kerala", "South", "682001"),
    ("Thiruvananthapuram", "Kerala", "South", "695001"),
    ("Delhi", "Delhi", "North", "110001"),
    ("Noida", "Uttar Pradesh", "North", "201301"),
    ("Lucknow", "Uttar Pradesh", "North", "226001"),
    ("Jaipur", "Rajasthan", "North", "302001"),
    ("Chandigarh", "Punjab", "North", "160001"),
    ("Kolkata", "West Bengal", "East", "700001"),
    ("Bhubaneswar", "Odisha", "East", "751001"),
    ("Patna", "Bihar", "East", "800001"),
    ("Ahmedabad", "Gujarat", "West", "380001"),
    ("Surat", "Gujarat", "West", "395001"),
    ("Indore", "Madhya Pradesh", "Central", "452001"),
    ("Bhopal", "Madhya Pradesh", "Central", "462001"),
]

FIRST_NAMES = [
    ("Aarav", "Male"), ("Vihaan", "Male"), ("Vivaan", "Male"), ("Ananya", "Female"), ("Diya", "Female"),
    ("Advik", "Male"), ("Kabir", "Male"), ("Aditi", "Female"), ("Pari", "Female"), ("Arjun", "Male"),
    ("Reyansh", "Male"), ("Rohan", "Male"), ("Priya", "Female"), ("Saanvi", "Female"), ("Isha", "Female"),
    ("Vikram", "Male"), ("Rahul", "Male"), ("Sneha", "Female"), ("Neha", "Female"), ("Pooja", "Female"),
    ("Siddharth", "Male"), ("Amitabh", "Male"), ("Divya", "Female"), ("Karan", "Male"), ("Tanvi", "Female"),
    ("Manish", "Male"), ("Sunita", "Female"), ("Rajesh", "Male"), ("Deepak", "Male"), ("Kavita", "Female"),
    ("Meera", "Female"), ("Harsh", "Male"), ("Ritu", "Female"), ("Suresh", "Male"), ("Ankit", "Male")
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Iyer", "Singh", "Gupta", "Nair", "Reddy", "Roy", "Joshi",
    "Rao", "Menon", "Chatterjee", "Deshmukh", "Malhotra", "Kapoor", "Bhatia", "Chauhan", "Kulkarni", "Aggarwal"
]

SEGMENTS = ["Consumer", "Consumer", "SMB", "Enterprise", "VIP"]
ACQUISITION_CHANNELS = ["Google Ads", "Organic Search", "Meta Ads", "Email Campaign", "Referral", "Affiliate"]
AGE_GROUPS = ["18-25", "26-35", "36-50", "50+"]
LTV_TIERS = ["High", "Medium", "Low"]

SELLERS_DATA = [
    ("SEL-101", "Apex Tech Solutions", "Apex Retail India Ltd", "Bengaluru", "Karnataka", 4.8, 0.08, "Warehouse Express"),
    ("SEL-102", "Bharat Electronics Hub", "Bharat Retailers Pvt Ltd", "Delhi", "Delhi", 4.6, 0.09, "Warehouse Express"),
    ("SEL-103", "Royal Fabric Creations", "Royal Textiles Ltd", "Surat", "Gujarat", 4.7, 0.12, "Seller Fulfilled"),
    ("SEL-104", "Heritage Living & Decor", "Heritage Home India", "Jaipur", "Rajasthan", 4.5, 0.10, "Seller Fulfilled"),
    ("SEL-105", "ProFit Footwear Co", "ProFit Sports Corp", "Mumbai", "Maharashtra", 4.9, 0.07, "Warehouse Express"),
    ("SEL-106", "KitchenCraft Appliances", "KitchenCraft India Pvt Ltd", "Pune", "Maharashtra", 4.4, 0.08, "Warehouse Express"),
    ("SEL-107", "Urban Luxe Accessories", "Urban Luxe Brands", "Kolkata", "West Bengal", 4.6, 0.11, "Seller Fulfilled"),
    ("SEL-108", "Zenith Audio & Visuals", "Zenith Electronics India", "Hyderabad", "Telangana", 4.8, 0.08, "Warehouse Express"),
    ("SEL-109", "Desi Trendz Lifestyle", "Desi Trendz Apparel Ltd", "Chennai", "Tamil Nadu", 4.5, 0.10, "Seller Fulfilled"),
    ("SEL-110", "Swift Logistics Gadgets", "Swift Digital Retail", "Noida", "Uttar Pradesh", 4.7, 0.09, "Warehouse Express"),
]

PRODUCTS_DATA = [
    # Smartphones & Tablets
    ("SKU-SMP-001", "Apple iPhone 15 Pro (256GB)", "Apple", "Electronics", "Smartphones", 112000.00, 134900.00, 45, 10, 4.8, 1240, 0.187, True),
    ("SKU-SMP-002", "Samsung Galaxy S24 Ultra", "Samsung", "Electronics", "Smartphones", 105000.00, 129999.00, 30, 8, 4.7, 890, 0.232, True),
    ("SKU-SMP-003", "OnePlus 12 5G (256GB)", "OnePlus", "Electronics", "Smartphones", 52000.00, 64999.00, 60, 15, 4.6, 1530, 0.220, True),
    ("SKU-SMP-004", "Google Pixel 8 Pro", "Google", "Electronics", "Smartphones", 78000.00, 96999.00, 25, 5, 4.5, 620, 0.213, False),
    ("SKU-SMP-005", "Apple iPad Air M2", "Apple", "Electronics", "Tablets", 48000.00, 59900.00, 40, 10, 4.8, 710, 0.460, True),
    ("SKU-SMP-006", "Xiaomi Redmi Note 13 Pro+", "Xiaomi", "Electronics", "Smartphones", 24000.00, 31999.00, 80, 20, 4.4, 2100, 0.204, False),
    
    # Laptops & Audio
    ("SKU-LAP-001", "MacBook Air 15-inch M3", "Apple", "Electronics", "Laptops", 115000.00, 134900.00, 20, 5, 4.9, 480, 1.510, True),
    ("SKU-LAP-002", "Dell XPS 15 OLED", "Dell", "Electronics", "Laptops", 132000.00, 154990.00, 3, 5, 4.6, 320, 1.860, False),
    ("SKU-LAP-003", "Lenovo ThinkPad X1 Carbon", "Lenovo", "Electronics", "Laptops", 128000.00, 149990.00, 18, 4, 4.7, 260, 1.120, False),
    ("SKU-AUD-001", "Sony WH-1000XM5 ANC Headphones", "Sony", "Electronics", "Audio", 22000.00, 29990.00, 75, 15, 4.8, 3100, 0.250, True),
    ("SKU-AUD-002", "Apple AirPods Pro (2nd Gen)", "Apple", "Electronics", "Audio", 18500.00, 24900.00, 90, 20, 4.8, 4200, 0.056, True),
    ("SKU-AUD-003", "Bose QuietComfort Ultra", "Bose", "Electronics", "Audio", 26000.00, 35900.00, 5, 10, 4.7, 850, 0.254, False),
    ("SKU-WCH-001", "Noise ColorFit Pro 5 Smartwatch", "Noise", "Electronics", "Wearables", 2100.00, 3499.00, 180, 30, 4.3, 5800, 0.045, False),
    ("SKU-WCH-002", "Apple Watch Series 9 GPS", "Apple", "Electronics", "Wearables", 34000.00, 41900.00, 40, 10, 4.8, 1400, 0.038, True),

    # Apparel & Fashion
    ("SKU-APP-001", "Fabindia Pure Silk Nehru Jacket", "Fabindia", "Apparel", "Men Ethnic", 3200.00, 5999.00, 50, 12, 4.6, 320, 0.350, False),
    ("SKU-APP-002", "Manyavar Chikankari Kurta Set", "Manyavar", "Apparel", "Men Ethnic", 2800.00, 4999.00, 65, 15, 4.7, 450, 0.400, True),
    ("SKU-APP-003", "Biba Anarkali Embroidered Suit", "Biba", "Apparel", "Women Ethnic", 3100.00, 5499.00, 70, 15, 4.5, 620, 0.450, True),
    ("SKU-APP-004", "Levi's 511 Slim Fit Jeans", "Levi's", "Apparel", "Men Western", 1800.00, 3299.00, 110, 25, 4.5, 1800, 0.600, False),
    ("SKU-APP-005", "Allen Solly Formal Cotton Shirt", "Allen Solly", "Apparel", "Men Western", 1100.00, 2199.00, 140, 30, 4.4, 1200, 0.280, False),
    ("SKU-APP-006", "W for Woman Printed Straight Kurta", "W", "Apparel", "Women Ethnic", 950.00, 1899.00, 95, 20, 4.3, 780, 0.220, False),

    # Footwear
    ("SKU-FTW-001", "Nike Air Zoom Pegasus 40", "Nike", "Footwear", "Running Shoes", 5800.00, 9695.00, 55, 12, 4.7, 980, 0.580, True),
    ("SKU-FTW-002", "Adidas Ultraboost Light", "Adidas", "Footwear", "Running Shoes", 8500.00, 13999.00, 40, 10, 4.8, 720, 0.610, True),
    ("SKU-FTW-003", "Puma Softride Rift Slip-On", "Puma", "Footwear", "Sneakers", 2200.00, 3999.00, 120, 25, 4.4, 2300, 0.480, False),
    ("SKU-FTW-004", "Red Chief Genuine Leather Boots", "Red Chief", "Footwear", "Formal & Boots", 2600.00, 4799.00, 45, 10, 4.5, 540, 0.850, False),

    # Home & Kitchen Appliances
    ("SKU-HOM-001", "Philips XXL Digital Air Fryer", "Philips", "Home & Kitchen", "Appliances", 7500.00, 12499.00, 40, 8, 4.6, 890, 4.200, True),
    ("SKU-HOM-002", "Instant Pot Duo 7-in-1 (6L)", "Instant Pot", "Home & Kitchen", "Cookware", 6200.00, 9999.00, 35, 8, 4.7, 650, 5.100, False),
    ("SKU-HOM-003", "Prestige Iris 750W Mixer Grinder", "Prestige", "Home & Kitchen", "Appliances", 2100.00, 3499.00, 130, 30, 4.3, 3400, 3.800, False),
    ("SKU-HOM-004", "Dyson V12 Detect Slim Vacuum", "Dyson", "Home & Kitchen", "Cleaning", 38000.00, 49900.00, 2, 3, 4.8, 310, 2.200, True),
    ("SKU-HOM-005", "Kent Grand Plus RO Water Purifier", "Kent", "Home & Kitchen", "Appliances", 11500.00, 16999.00, 4, 6, 4.5, 1420, 7.500, False),

    # Accessories & Travel
    ("SKU-ACC-001", "Wildcraft 45L Trail Backpack", "Wildcraft", "Accessories", "Bags & Luggage", 1400.00, 2699.00, 85, 20, 4.4, 1100, 0.720, False),
    ("SKU-ACC-002", "American Tourister 68cm Trolley", "American Tourister", "Accessories", "Bags & Luggage", 3800.00, 6999.00, 60, 15, 4.6, 950, 3.400, True),
    ("SKU-ACC-003", "Ray-Ban Aviator Polarized Sunglasses", "Ray-Ban", "Accessories", "Eyewear", 6100.00, 9890.00, 50, 10, 4.7, 760, 0.120, True),
]

CARRIERS = ["BlueDart", "Delhivery", "FedEx", "Ecom Express", "India Post"]
PAYMENT_METHODS = ["UPI", "Credit Card", "Net Banking", "Debit Card", "EMI", "Cash on Delivery"]
ORDER_STATUSES = ["Delivered", "Delivered", "Delivered", "Completed", "Processing", "Cancelled", "Returned"]
COUPONS = ["SAVE10", "WELCOME15", "FESTIVE20", "DIWALI500", "TECHMEGA", None, None, None]


async def seed_enterprise_database():
    url = clean_db_url(settings.DATABASE_URL)
    print(f"[INIT] Connecting to PostgreSQL at {url.split('@')[-1]}...")
    conn = await asyncpg.connect(url)

    try:
        print("[SCHEMA] Recreating enterprise relational tables & indexes...")
        await conn.execute("""
        DROP TABLE IF EXISTS shipments CASCADE;
        DROP TABLE IF EXISTS order_items CASCADE;
        DROP TABLE IF EXISTS orders CASCADE;
        DROP TABLE IF EXISTS products CASCADE;
        DROP TABLE IF EXISTS sellers CASCADE;
        DROP TABLE IF EXISTS customers CASCADE;

        -- 1. Customers Table (Rich Demographics & Acquisition Attributes)
        CREATE TABLE customers (
            id SERIAL PRIMARY KEY,
            customer_code VARCHAR(30) UNIQUE NOT NULL,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            phone VARCHAR(20) NOT NULL,
            gender VARCHAR(10) NOT NULL,
            age_group VARCHAR(20) NOT NULL,
            city VARCHAR(50) NOT NULL,
            state VARCHAR(50) NOT NULL,
            region VARCHAR(20) NOT NULL,
            postal_code VARCHAR(10) NOT NULL,
            country VARCHAR(30) NOT NULL DEFAULT 'India',
            customer_segment VARCHAR(30) NOT NULL,
            acquisition_channel VARCHAR(40) NOT NULL,
            lifetime_value_tier VARCHAR(20) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            signup_date DATE NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        );

        -- 2. Sellers Table
        CREATE TABLE sellers (
            id SERIAL PRIMARY KEY,
            seller_code VARCHAR(30) UNIQUE NOT NULL,
            seller_name VARCHAR(100) NOT NULL,
            business_name VARCHAR(120) NOT NULL,
            city VARCHAR(50) NOT NULL,
            state VARCHAR(50) NOT NULL,
            rating NUMERIC(3, 2) NOT NULL,
            commission_rate NUMERIC(4, 3) NOT NULL,
            fulfillment_type VARCHAR(40) NOT NULL
        );

        -- 3. Products Table (Wide Catalog Hierarchy & Inventory Health)
        CREATE TABLE products (
            id SERIAL PRIMARY KEY,
            sku VARCHAR(40) UNIQUE NOT NULL,
            product_name VARCHAR(120) NOT NULL,
            brand VARCHAR(60) NOT NULL,
            primary_category VARCHAR(50) NOT NULL,
            sub_category VARCHAR(50) NOT NULL,
            category VARCHAR(50),
            cost_price NUMERIC(10, 2) NOT NULL,
            selling_price NUMERIC(10, 2) NOT NULL,
            discount_percentage NUMERIC(5, 2) NOT NULL DEFAULT 0,
            margin_amount NUMERIC(10, 2) NOT NULL,
            stock_quantity INT NOT NULL,
            reorder_level INT NOT NULL,
            rating NUMERIC(3, 2) NOT NULL,
            review_count INT NOT NULL DEFAULT 0,
            weight_kg NUMERIC(6, 3) NOT NULL DEFAULT 0.5,
            is_featured BOOLEAN NOT NULL DEFAULT FALSE,
            created_at DATE NOT NULL DEFAULT '2023-01-01'
        );

        -- 4. Orders Table (Deep Financial & Operational Metrics)
        CREATE TABLE orders (
            id SERIAL PRIMARY KEY,
            order_number VARCHAR(40) UNIQUE NOT NULL,
            customer_id INT REFERENCES customers(id),
            seller_id INT REFERENCES sellers(id),
            order_date DATE NOT NULL,
            order_timestamp TIMESTAMP NOT NULL,
            status VARCHAR(30) NOT NULL,
            order_status VARCHAR(30),
            payment_method VARCHAR(30) NOT NULL,
            payment_status VARCHAR(30) NOT NULL,
            currency VARCHAR(10) NOT NULL DEFAULT 'INR',
            subtotal_amount NUMERIC(12, 2) NOT NULL,
            subtotal NUMERIC(12, 2),
            discount_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
            tax_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
            shipping_fee NUMERIC(8, 2) NOT NULL DEFAULT 0,
            total_amount NUMERIC(12, 2) NOT NULL,
            coupon_code VARCHAR(30),
            shipping_city VARCHAR(50) NOT NULL,
            shipping_state VARCHAR(50) NOT NULL,
            delivery_days INT,
            is_first_order BOOLEAN NOT NULL DEFAULT FALSE
        );

        -- 5. Order Items Table (Granular Margin & Line Item Accounting)
        CREATE TABLE order_items (
            id SERIAL PRIMARY KEY,
            order_id INT REFERENCES orders(id) ON DELETE CASCADE,
            product_id INT REFERENCES products(id),
            quantity INT NOT NULL,
            unit_cost_price NUMERIC(10, 2) NOT NULL,
            unit_selling_price NUMERIC(10, 2) NOT NULL,
            item_discount NUMERIC(10, 2) NOT NULL DEFAULT 0,
            total_item_revenue NUMERIC(12, 2) NOT NULL,
            total_price NUMERIC(12, 2),
            item_profit_margin NUMERIC(12, 2) NOT NULL,
            return_status VARCHAR(30) NOT NULL DEFAULT 'None'
        );

        -- 6. Shipments Table (Logistics & Delivery Carrier SLA)
        CREATE TABLE shipments (
            id SERIAL PRIMARY KEY,
            order_id INT UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
            carrier VARCHAR(50) NOT NULL,
            tracking_number VARCHAR(50) UNIQUE NOT NULL,
            status VARCHAR(30) NOT NULL,
            dispatch_date DATE,
            delivery_date DATE,
            shipping_cost_inr NUMERIC(8, 2) NOT NULL
        );

        -- Performance Indexes
        CREATE INDEX idx_customers_state_segment ON customers(state, customer_segment);
        CREATE INDEX idx_customers_channel ON customers(acquisition_channel);
        CREATE INDEX idx_products_category ON products(primary_category, sub_category);
        CREATE INDEX idx_products_brand ON products(brand);
        CREATE INDEX idx_orders_customer_id ON orders(customer_id);
        CREATE INDEX idx_orders_seller_id ON orders(seller_id);
        CREATE INDEX idx_orders_date ON orders(order_date);
        CREATE INDEX idx_orders_status ON orders(status);
        CREATE INDEX idx_orders_payment ON orders(payment_method);
        CREATE INDEX idx_order_items_order_id ON order_items(order_id);
        CREATE INDEX idx_order_items_product_id ON order_items(product_id);
        CREATE INDEX idx_shipments_carrier ON shipments(carrier);
        """)

        # Insert Sellers
        print("[DATA] Inserting 10 enterprise sellers...")
        for s in SELLERS_DATA:
            await conn.execute(
                """
                INSERT INTO sellers (seller_code, seller_name, business_name, city, state, rating, commission_rate, fulfillment_type)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8);
                """,
                s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7]
            )

        # Insert Products
        print("[DATA] Inserting 32 rich multi-attribute product SKUs...")
        for p in PRODUCTS_DATA:
            margin = p[6] - p[5]
            disc_pct = round((p[6] - p[5]) / p[6] * 10, 1)
            await conn.execute(
                """
                INSERT INTO products (sku, product_name, brand, primary_category, sub_category, category, cost_price, selling_price,
                                     discount_percentage, margin_amount, stock_quantity, reorder_level, rating, review_count, weight_kg, is_featured)
                VALUES ($1, $2, $3, $4, $5, $4, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15);
                """,
                p[0], p[1], p[2], p[3], p[4], p[5], p[6], disc_pct, margin, p[7], p[8], p[9], p[10], p[11], p[12]
            )

        # Generate 150 Customers
        print("[DATA] Generating 150 multi-attribute customer profiles across all regions...")
        cust_records = []
        base_signup = datetime(2023, 1, 1)

        for i in range(1, 151):
            fn, gender = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            full_name = f"{fn} {ln}"
            code = f"CUST-{i:04d}"
            email = f"{fn.lower()}.{ln.lower()}{i}@example.in"
            phone = f"+91-{random.randint(7000000000, 9999999999)}"
            city, state, region, pin = random.choice(CITIES_STATES)
            segment = random.choice(SEGMENTS)
            channel = random.choice(ACQUISITION_CHANNELS)
            age_group = random.choice(AGE_GROUPS)
            ltv_tier = random.choice(LTV_TIERS)
            signup_date = (base_signup + timedelta(days=random.randint(0, 750))).date()

            cust_records.append((
                code, fn, ln, full_name, email, phone, gender, age_group,
                city, state, region, pin, segment, channel, ltv_tier, signup_date
            ))

        for c in cust_records:
            await conn.execute(
                """
                INSERT INTO customers (customer_code, first_name, last_name, full_name, email, phone, gender, age_group,
                                      city, state, region, postal_code, customer_segment, acquisition_channel, lifetime_value_tier, signup_date)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16);
                """,
                *c
            )

        # Retrieve IDs
        customer_rows = await conn.fetch("SELECT id, city, state, signup_date FROM customers;")
        seller_ids = [r["id"] for r in await conn.fetch("SELECT id FROM sellers;")]
        product_rows = await conn.fetch("SELECT id, cost_price, selling_price FROM products;")
        products_dict = {r["id"]: (float(r["cost_price"]), float(r["selling_price"])) for r in product_rows}
        product_ids = list(products_dict.keys())

        # Generate 1,500 Orders & 4,500 Order Items across 2023-2025
        print("[DATA] Synthesizing 1,500 enterprise orders with balanced margins, taxes, and shipping fees...")
        order_start = datetime(2023, 2, 1)

        for ord_idx in range(1, 1501):
            c_info = random.choice(customer_rows)
            c_id = c_info["id"]
            seller_id = random.choice(seller_ids)

            # Order Date after customer signup
            cust_signup = c_info["signup_date"]
            days_since_signup = (datetime(2025, 9, 20).date() - cust_signup).days
            days_offset = random.randint(0, max(0, days_since_signup))
            order_date = cust_signup + timedelta(days=days_offset)
            order_timestamp = datetime.combine(order_date, datetime.min.time()) + timedelta(
                hours=random.randint(8, 22), minutes=random.randint(0, 59), seconds=random.randint(0, 59)
            )

            status = random.choice(ORDER_STATUSES)
            pm = random.choice(PAYMENT_METHODS)
            pay_status = "Paid" if status in ["Delivered", "Completed", "Processing"] else ("Refunded" if status == "Returned" else "Failed")
            coupon = random.choice(COUPONS)
            delivery_days = random.randint(2, 6) if status in ["Delivered", "Completed", "Returned"] else None
            is_first = (ord_idx % 15 == 0)
            order_num = f"ORD-{order_date.year}-{ord_idx:05d}"

            # Pick 1 to 4 items per order
            num_items = random.randint(1, 4)
            chosen_prods = random.sample(product_ids, k=num_items)

            subtotal = 0.0
            order_item_tuples = []

            for p_id in chosen_prods:
                c_price, s_price = products_dict[p_id]
                qty = random.randint(1, 3)
                item_disc = random.choice([0.0, 0.0, 100.0, 250.0, 500.0])
                item_rev = (s_price * qty) - item_disc
                profit_margin = item_rev - (c_price * qty)
                ret_status = "Returned" if status == "Returned" else "None"

                subtotal += item_rev
                order_item_tuples.append((p_id, qty, c_price, s_price, item_disc, item_rev, item_rev, profit_margin, ret_status))

            # Financial Totals Calculation
            discount_amount = 500.0 if coupon == "DIWALI500" else (round(subtotal * 0.10, 2) if coupon == "SAVE10" else (round(subtotal * 0.15, 2) if coupon == "WELCOME15" else 0.0))
            tax_amount = round((subtotal - discount_amount) * 0.18, 2)  # 18% GST
            shipping_fee = 0.0 if subtotal > 1500 else 149.0
            total_amount = round((subtotal - discount_amount) + tax_amount + shipping_fee, 2)

            # Insert Order
            order_id = await conn.fetchval(
                """
                INSERT INTO orders (order_number, customer_id, seller_id, order_date, order_timestamp, status, order_status,
                                   payment_method, payment_status, subtotal_amount, subtotal, discount_amount, tax_amount,
                                   shipping_fee, total_amount, coupon_code, shipping_city, shipping_state, delivery_days, is_first_order)
                VALUES ($1, $2, $3, $4, $5, $6, $6, $7, $8, $9, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
                RETURNING id;
                """,
                order_num, c_id, seller_id, order_date, order_timestamp, status,
                pm, pay_status, subtotal, discount_amount, tax_amount,
                shipping_fee, total_amount, coupon, c_info["city"], c_info["state"], delivery_days, is_first
            )

            # Insert Order Items
            for item in order_item_tuples:
                await conn.execute(
                    """
                    INSERT INTO order_items (order_id, product_id, quantity, unit_cost_price, unit_selling_price,
                                           item_discount, total_item_revenue, total_price, item_profit_margin, return_status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10);
                    """,
                    order_id, item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8]
                )

            # Insert Shipment record
            carrier = random.choice(CARRIERS)
            tracking = f"TRK-{carrier[:3].upper()}-{ord_idx:06d}"
            disp_date = order_date + timedelta(days=1)
            deliv_date = disp_date + timedelta(days=delivery_days) if delivery_days else None
            ship_status = "Delivered" if status in ["Delivered", "Completed"] else ("In Transit" if status == "Processing" else "Cancelled")
            ship_cost = random.choice([80.0, 120.0, 150.0, 200.0])

            await conn.execute(
                """
                INSERT INTO shipments (order_id, carrier, tracking_number, status, dispatch_date, delivery_date, shipping_cost_inr)
                VALUES ($1, $2, $3, $4, $5, $6, $7);
                """,
                order_id, carrier, tracking, ship_status, disp_date, deliv_date, ship_cost
            )

        # Verification Statistics
        c_cnt = await conn.fetchval("SELECT COUNT(*) FROM customers;")
        s_cnt = await conn.fetchval("SELECT COUNT(*) FROM sellers;")
        p_cnt = await conn.fetchval("SELECT COUNT(*) FROM products;")
        o_cnt = await conn.fetchval("SELECT COUNT(*) FROM orders;")
        oi_cnt = await conn.fetchval("SELECT COUNT(*) FROM order_items;")
        sh_cnt = await conn.fetchval("SELECT COUNT(*) FROM shipments;")
        tot_rev = await conn.fetchval("SELECT SUM(total_amount) FROM orders WHERE status IN ('Delivered', 'Completed');")
        tot_profit = await conn.fetchval("SELECT SUM(item_profit_margin) FROM order_items WHERE return_status = 'None';")

        print("[OK] Enterprise Seeding Complete!")
        print(f"[STATS] {c_cnt} Customers | {s_cnt} Sellers | {p_cnt} Products | {o_cnt} Orders | {oi_cnt} Order Items | {sh_cnt} Shipments")
        print(f"[METRICS] Total Delivered/Completed Revenue: Rs. {tot_rev:,.2f}")
        print(f"[METRICS] Total Net Profit Margin Generated: Rs. {tot_profit:,.2f}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed_enterprise_database())
