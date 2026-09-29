import pytest
from app.database import get_schema_summary, validate_safe_sql, execute_safe_sql
from app.llm import generate_query_decision
from app.models import ChatMessage


@pytest.mark.asyncio
async def test_schema_summary():
    summary = await get_schema_summary()
    assert "customers" in summary
    assert "products" in summary
    assert "orders" in summary
    assert "order_items" in summary
    assert "Relationships" in summary


@pytest.mark.asyncio
async def test_sql_safety_validation():
    # Valid SELECT
    safe, clean = validate_safe_sql("SELECT name, city FROM customers LIMIT 5;")
    assert safe is True
    assert "LIMIT 5" in clean

    # Destructive operations
    unsafe_drop, err1 = validate_safe_sql("DROP TABLE customers;")
    assert unsafe_drop is False
    assert "blocked" in err1.lower() or "read-only" in err1.lower()

    unsafe_delete, err2 = validate_safe_sql("DELETE FROM orders WHERE id = 1;")
    assert unsafe_delete is False

    unsafe_inject, err3 = validate_safe_sql("SELECT 1; DROP TABLE products;")
    assert unsafe_inject is False


@pytest.mark.asyncio
async def test_normal_query_execution():
    # Execute valid SQL
    sql = "SELECT primary_category, count(*) as count FROM products GROUP BY primary_category ORDER BY count DESC;"
    cols, rows, exec_time = await execute_safe_sql(sql)
    assert len(cols) == 2
    assert "primary_category" in cols
    assert "count" in cols
    assert len(rows) > 0
    assert exec_time >= 0


@pytest.mark.asyncio
async def test_ambiguity_detection_and_clarification():
    # Ambiguous question
    schema = await get_schema_summary()
    decision = await generate_query_decision("Who are our top customers?", schema, [])
    assert decision.is_ambiguous is True
    assert decision.clarification_question is not None
    assert len(decision.clarification_options) >= 2
    assert decision.sql is None

    # Follow-up with clarification choice
    follow_up = await generate_query_decision(
        "By total revenue spent",
        schema,
        [
            ChatMessage(role="user", content="Who are our top customers?"),
            ChatMessage(role="assistant", content=decision.clarification_question)
        ]
    )
    assert follow_up.is_ambiguous is False
    assert follow_up.sql is not None
    assert "SELECT" in follow_up.sql.upper()

    # Execute the generated SQL
    cols, rows, exec_time = await execute_safe_sql(follow_up.sql)
    assert len(rows) > 0
