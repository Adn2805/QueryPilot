import os
import psycopg2
from psycopg2.extras import execute_batch

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "querypilot")
DB_PASSWORD = os.getenv("DB_PASSWORD", "querypilot_password")
DB_NAME = os.getenv("APP_DB_NAME", "querypilot_app")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

def seed_glossary_terms():
    terms = [
        (
            'GMV', 
            'Gross Merchandise Value — total value of all orders regardless of status.',
            'SUM(orders.total_amount)',
            ['orders'],
            ['total_amount']
        ),
        (
            'Net Revenue',
            'Revenue after discounts and returns.',
            "SUM(orders.total_amount - orders.discount_amount) WHERE status NOT IN ('cancelled', 'returned')",
            ['orders'],
            ['total_amount', 'discount_amount', 'status']
        ),
        (
            'Active Customer',
            'A customer with at least one completed order in the previous 90 days',
            "COUNT(DISTINCT CASE WHEN orders.status = 'completed' AND orders.order_date >= CURRENT_DATE - INTERVAL '90 days' THEN orders.customer_id END) > 0",
            ['orders', 'customers'],
            ['status', 'order_date', 'customer_id']
        ),
        (
            'High-value Customer',
            'A customer whose total completed order value exceeds ₹1,00,000',
            "SUM(CASE WHEN orders.status = 'completed' THEN orders.total_amount ELSE 0 END) > 100000",
            ['orders', 'customers'],
            ['status', 'total_amount', 'customer_id']
        ),
        (
            'Average Order Value (AOV)',
            'Average total_amount per completed order',
            "AVG(orders.total_amount) WHERE status = 'completed'",
            ['orders'],
            ['total_amount', 'status']
        ),
        (
            'Repeat Customer',
            'A customer with more than one completed order',
            "COUNT(CASE WHEN orders.status = 'completed' THEN 1 END) > 1",
            ['orders', 'customers'],
            ['status', 'customer_id']
        ),
        (
            'Product margin',
            '(price - cost) / price * 100',
            "(products.price - products.cost) / products.price * 100",
            ['products'],
            ['price', 'cost']
        ),
        (
            'Conversion Rate',
            'completed orders / total orders',
            "COUNT(CASE WHEN status = 'completed' THEN 1 END)::FLOAT / NULLIF(COUNT(*), 0)",
            ['orders'],
            ['status']
        )
    ]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            INSERT INTO glossary_terms (term, definition, sql_expression, related_tables, related_columns)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (term) DO UPDATE SET 
                definition = EXCLUDED.definition,
                sql_expression = EXCLUDED.sql_expression,
                related_tables = EXCLUDED.related_tables,
                related_columns = EXCLUDED.related_columns
        """
        execute_batch(cursor, query, terms)
        conn.commit()
        print("Glossary terms seeded successfully!")
    except Exception as e:
        conn.rollback()
        print(f"Error seeding glossary terms: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    seed_glossary_terms()
