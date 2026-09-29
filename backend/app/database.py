import asyncio
import re
import time
import datetime
from decimal import Decimal
from typing import List, Dict, Any, Tuple
import asyncpg
from app.config import settings

# Global asyncpg pool
_pool: asyncpg.Pool | None = None


def clean_db_url(url: str) -> str:
    """Normalize SQLAlchemy/asyncpg connection string to standard asyncpg format."""
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql://", 1)
    return url


async def get_db_pool() -> asyncpg.Pool:
    global _pool
    current_loop = asyncio.get_running_loop()
    if _pool is None or _pool._loop != current_loop or _pool._closed:
        url = clean_db_url(settings.DATABASE_URL)
        _pool = await asyncpg.create_pool(dsn=url, min_size=1, max_size=10, command_timeout=settings.QUERY_TIMEOUT_SECONDS)
    return _pool


async def close_db_pool():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def get_schema_summary() -> str:
    """
    Introspects the PostgreSQL database schema and returns a clear,
    markdown-formatted summary suitable for LLM system prompts.
    """
    pool = await get_db_pool()
    query = """
    SELECT 
        c.table_name,
        c.column_name,
        c.data_type,
        c.is_nullable
    FROM information_schema.columns c
    JOIN information_schema.tables t 
      ON c.table_name = t.table_name AND c.table_schema = t.table_schema
    WHERE c.table_schema = 'public'
      AND t.table_type = 'BASE TABLE'
      AND c.table_name IN ('customers', 'sellers', 'products', 'orders', 'order_items', 'shipments')
    ORDER BY c.table_name, c.ordinal_position;
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(query)

    if not rows:
        return "No enterprise tables found in the database."

    schema_dict: Dict[str, List[str]] = {}
    for r in rows:
        tbl = r["table_name"]
        col = f"{r['column_name']} ({r['data_type']})"
        if tbl not in schema_dict:
            schema_dict[tbl] = []
        schema_dict[tbl].append(col)

    schema_lines = ["### Enterprise Database Schema (PostgreSQL):"]
    for tbl in ['customers', 'sellers', 'products', 'orders', 'order_items', 'shipments']:
        if tbl in schema_dict:
            schema_lines.append(f"- **Table `{tbl}`**: {', '.join(schema_dict[tbl])}")

    # Add foreign key relationship context for enterprise data model
    schema_lines.append("\n### Relationships & Foreign Keys:")
    schema_lines.append("- `orders.customer_id` references `customers.id`")
    schema_lines.append("- `orders.seller_id` references `sellers.id`")
    schema_lines.append("- `order_items.order_id` references `orders.id`")
    schema_lines.append("- `order_items.product_id` references `products.id`")
    schema_lines.append("- `shipments.order_id` references `orders.id`")

    schema_lines.append("\n### Domain Knowledge & Column Aliases:")
    schema_lines.append("- **Categories**: `products.primary_category` (or `products.category`), `products.sub_category`, `products.brand`")
    schema_lines.append("- **Profitability**: `order_items.item_profit_margin` = revenue minus cost; `products.margin_amount` = `selling_price` - `cost_price`")
    schema_lines.append("- **Revenue**: `orders.total_amount`, `order_items.total_item_revenue` (or `order_items.total_price`)")
    schema_lines.append("- **Logistics**: `shipments.carrier` (BlueDart, Delhivery, FedEx, Ecom Express, India Post); `orders.delivery_days`")
    schema_lines.append("- **Marketing**: `customers.acquisition_channel` (Google Ads, Meta Ads, Organic Search, Email Campaign, Referral, Affiliate); `customers.customer_segment` (Enterprise, SMB, Consumer, VIP)")
    schema_lines.append("- **Inventory Health**: `products.stock_quantity`, `products.reorder_level` (Stockout Risk when `stock_quantity <= reorder_level`)")
    schema_lines.append("- **Fulfillment**: `orders.status` / `orders.order_status` ('Delivered', 'Completed', 'Processing', 'Cancelled', 'Returned')")
    schema_lines.append(f"- **Currency**: INR ({settings.DEFAULT_CURRENCY_SYMBOL})")

    return "\n".join(schema_lines)


def validate_safe_sql(sql: str) -> Tuple[bool, str]:
    """
    Ensures the SQL query is strictly read-only (SELECT / WITH) and contains no
    destructive or mutating statements.
    """
    clean_sql = sql.strip().rstrip(";").strip()

    # Disallow multiple statements separated by semicolon
    if ";" in clean_sql:
        return False, "Multiple SQL statements are disallowed for security."

    # Check that query starts with SELECT or WITH
    upper_sql = clean_sql.upper()
    if not (upper_sql.startswith("SELECT") or upper_sql.startswith("WITH")):
        return False, "Only read-only SELECT or WITH (CTE) queries are permitted."

    # Dangerous DDL / DML keywords - check against SQL structure (ignoring string literals like 'Vacuum Cleaner')
    sql_without_strings = re.sub(r"'(?:''|[^'])*'", "''", clean_sql)
    upper_structure = sql_without_strings.upper()

    forbidden_patterns = [
        r"\bDROP\b", r"\bDELETE\b", r"\bINSERT\b", r"\bUPDATE\b",
        r"\bTRUNCATE\b", r"\bALTER\b", r"\bCREATE\b", r"\bGRANT\b",
        r"\bREVOKE\b", r"\bEXEC\b", r"\bEXECUTE\b", r"\bCOPY\b",
        r"\bVACUUM\b", r"\bCOMMENT\b", r"\bRENAME\b"
    ]

    for pattern in forbidden_patterns:
        if re.search(pattern, upper_structure):
            return False, f"Mutating / destructive operations are blocked for security."

    return True, clean_sql


def serialize_cell(val: Any) -> Any:
    """Format non-JSON serializable values like Decimal, date, datetime."""
    if isinstance(val, (datetime.date, datetime.datetime)):
        return val.isoformat()
    if isinstance(val, Decimal):
        return float(val)
    return val


async def execute_safe_sql(sql: str) -> Tuple[List[str], List[Dict[str, Any]], float]:
    """
    Validates, limits, and executes a read-only SQL query against PostgreSQL.
    Returns: (column_names, rows_as_dicts, execution_time_ms)
    """
    is_safe, clean_or_err = validate_safe_sql(sql)
    if not is_safe:
        raise ValueError(clean_or_err)

    query = clean_or_err
    # Append LIMIT if missing
    if not re.search(r"\bLIMIT\s+\d+", query, re.IGNORECASE):
        query = f"{query} LIMIT {settings.MAX_ROWS}"

    pool = await get_db_pool()
    start_time = time.perf_counter()

    async with pool.acquire() as conn:
        stmt = await conn.prepare(query)
        records = await stmt.fetch()
        attributes = stmt.get_attributes()
        columns = [attr.name for attr in attributes] if attributes else []

    exec_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

    if not records:
        return columns, [], exec_time_ms

    rows = [
        {col: serialize_cell(row[col]) for col in columns}
        for row in records
    ]

    return columns, rows, exec_time_ms
