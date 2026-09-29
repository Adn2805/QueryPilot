import os
import random
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import execute_batch

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "querypilot")
DB_PASSWORD = os.getenv("DB_PASSWORD", "querypilot_password")
DB_NAME = os.getenv("DB_NAME", "querypilot_analytics")

# Seed setup
random.seed(42)

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

def seed_regions(cursor):
    regions = [
        ('Delhi', 'North'), ('Uttar Pradesh', 'North'), ('Punjab', 'North'), ('Rajasthan', 'North'),
        ('Karnataka', 'South'), ('Tamil Nadu', 'South'), ('Kerala', 'South'), ('Telangana', 'South'),
        ('West Bengal', 'East'), ('Odisha', 'East'),
        ('Maharashtra', 'West'), ('Gujarat', 'West')
    ]
    execute_batch(cursor, "INSERT INTO regions (region_name, zone) VALUES (%s, %s)", regions)

def seed_categories(cursor):
    categories = [
        ('Electronics', 'Gadgets and devices'),
        ('Clothing', 'Apparel and accessories'),
        ('Home & Kitchen', 'Home appliances and decor'),
        ('Books', 'Physical and digital books'),
        ('Sports', 'Sporting goods'),
        ('Beauty', 'Cosmetics and personal care'),
        ('Toys', 'Toys and games for kids'),
        ('Food & Beverages', 'Groceries and drinks'),
        ('Automotive', 'Car and bike accessories'),
        ('Office Supplies', 'Stationery and office equipment')
    ]
    execute_batch(cursor, "INSERT INTO categories (category_name, description) VALUES (%s, %s) RETURNING category_id", categories)
    return cursor.fetchall()

def seed_products(cursor, categories_ids):
    products = []
    for _ in range(200):
        category_id = random.choice(categories_ids)[0]
        # Basic mock product names based on categories
        product_name = f"Product {random.randint(1000, 9999)} - {category_id}"
        
        if category_id == 1: # Electronics
            price = random.uniform(999, 150000)
        elif category_id == 2: # Clothing
            price = random.uniform(299, 15000)
        elif category_id == 3: # Home & Kitchen
            price = random.uniform(499, 25000)
        elif category_id == 4: # Books
            price = random.uniform(99, 2500)
        else:
            price = random.uniform(100, 10000)
            
        cost = price * random.uniform(0.4, 0.8)
        stock_quantity = random.randint(0, 1000)
        created_date = datetime(2022, 1, 1).date() + timedelta(days=random.randint(0, 365))
        products.append((product_name, category_id, round(price, 2), round(cost, 2), stock_quantity, True, created_date))
        
    execute_batch(cursor, "INSERT INTO products (product_name, category_id, price, cost, stock_quantity, is_active, created_date) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING product_id, price", products)
    return cursor.fetchall()

def seed_customers(cursor):
    customers = []
    cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad', 'Pune', 'Kolkata', 'Jaipur', 'Ahmedabad', 'Lucknow']
    segments = ['Enterprise', 'SMB', 'Consumer']
    for i in range(500):
        name = f"Customer {i}"
        email = f"customer{i}@example.com"
        phone = f"98765{random.randint(10000, 99999)}"
        city = random.choice(cities)
        state = 'State' # Simplification
        region_id = random.randint(1, 12)
        segment = random.choices(segments, weights=[10, 30, 60])[0]
        signup_date = datetime(2022, 1, 1).date() + timedelta(days=random.randint(0, 1000))
        customers.append((name, email, phone, city, state, region_id, segment, signup_date))
        
    execute_batch(cursor, "INSERT INTO customers (customer_name, email, phone, city, state, region_id, segment, signup_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING customer_id", customers)
    return cursor.fetchall()

def seed_employees(cursor):
    employees = []
    departments = ['Sales', 'Support', 'Operations']
    for i in range(50):
        name = f"Employee {i}"
        department = random.choice(departments)
        role = "Staff"
        region_id = random.randint(1, 12)
        hire_date = datetime(2021, 1, 1).date() + timedelta(days=random.randint(0, 1000))
        employees.append((name, department, role, region_id, hire_date))
        
    execute_batch(cursor, "INSERT INTO employees (employee_name, department, role, region_id, hire_date) VALUES (%s, %s, %s, %s, %s) RETURNING employee_id", employees)
    return cursor.fetchall()

def seed_orders_and_items(cursor, customers_ids, products_info, employees_ids):
    statuses = ['completed', 'pending', 'cancelled', 'returned', 'processing']
    status_weights = [70, 10, 10, 5, 5]
    payment_methods = ['upi', 'credit_card', 'debit_card', 'net_banking', 'cod', 'wallet']
    payment_weights = [35, 20, 15, 15, 10, 5]
    
    start_date = datetime(2023, 1, 1).date()
    end_date = datetime(2026, 6, 30).date()
    date_range = (end_date - start_date).days
    
    orders = []
    order_items = []
    payments = []
    
    for i in range(5000):
        customer_id = random.choice(customers_ids)[0]
        # Skew dates towards more recent
        days_offset = int(date_range * (1 - random.random()**2))
        order_date = start_date + timedelta(days=days_offset)
        status = random.choices(statuses, weights=status_weights)[0]
        payment_method = random.choices(payment_methods, weights=payment_weights)[0]
        employee_id = random.choice(employees_ids)[0]
        
        # Generate items first to calculate total
        num_items = random.randint(1, 5)
        total_amount = 0
        current_order_items = []
        for _ in range(num_items):
            product = random.choice(products_info)
            product_id = product[0]
            unit_price = float(product[1])
            quantity = random.randint(1, 3)
            total_price = unit_price * quantity
            total_amount += total_price
            current_order_items.append((i+1, product_id, quantity, unit_price, total_price))
            
        discount = float(total_amount) * random.uniform(0, 0.2) if random.random() > 0.5 else 0.0
        final_amount = total_amount - discount
        
        orders.append((customer_id, order_date, status, total_amount, discount, payment_method, employee_id))
        order_items.extend(current_order_items)
        
        payment_status = 'completed' if status == 'completed' else ('failed' if status == 'cancelled' else 'pending')
        payments.append((i+1, final_amount, payment_status, order_date, payment_method))

    print("Executing orders insertion...")
    execute_batch(cursor, "INSERT INTO orders (customer_id, order_date, status, total_amount, discount_amount, payment_method, employee_id) VALUES (%s, %s, %s, %s, %s, %s, %s)", orders)
    print("Executing order_items insertion...")
    execute_batch(cursor, "INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price) VALUES (%s, %s, %s, %s, %s)", order_items)
    print("Executing payments insertion...")
    execute_batch(cursor, "INSERT INTO payments (order_id, amount, payment_status, payment_date, payment_method) VALUES (%s, %s, %s, %s, %s)", payments)

def main():
    print("Connecting to db...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("Seeding regions...")
        seed_regions(cursor)
        print("Seeding categories...")
        categories_ids = seed_categories(cursor)
        print("Seeding products...")
        products_info = seed_products(cursor, categories_ids)
        print("Seeding customers...")
        customers_ids = seed_customers(cursor)
        print("Seeding employees...")
        employees_ids = seed_employees(cursor)
        print("Seeding orders, items, payments...")
        seed_orders_and_items(cursor, customers_ids, products_info, employees_ids)
        
        conn.commit()
        print("Seeding complete!")
    except Exception as e:
        conn.rollback()
        print(f"Error seeding data: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
