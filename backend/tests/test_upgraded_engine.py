import pytest
from app.database import get_schema_summary, validate_safe_sql, execute_safe_sql
from app.llm import generate_query_decision
from app.models import ChatMessage, QueryRequest
from app.main import extract_kpi_metrics, resolve_robust_chart_type


@pytest.mark.asyncio
async def test_kpi_single_value_revenue():
    schema = await get_schema_summary()
    decision = await generate_query_decision("What is our total revenue in 2025?", schema, [])
    assert decision.is_supported is True
    assert decision.is_ambiguous is False
    assert decision.is_kpi is True
    assert decision.sql is not None

    cols, rows, exec_time = await execute_safe_sql(decision.sql)
    assert len(rows) == 1
    assert "total_revenue_inr" in cols

    kpis = extract_kpi_metrics(cols, rows, "₹")
    assert len(kpis) >= 1
    assert "₹" in kpis[0].formatted


@pytest.mark.asyncio
async def test_category_bar_chart():
    schema = await get_schema_summary()
    decision = await generate_query_decision("Show revenue by product category", schema, [])
    assert decision.is_supported is True
    assert decision.is_ambiguous is False
    assert decision.chart_type == "bar"
    assert decision.x_axis in ["primary_category", "category"]
    assert decision.y_axis == "total_revenue_inr"

    cols, rows, exec_time = await execute_safe_sql(decision.sql)
    assert len(rows) > 0
    assert any(c in cols for c in ["primary_category", "category"])
    assert "total_revenue_inr" in cols


@pytest.mark.asyncio
async def test_monthly_sales_line_chart():
    schema = await get_schema_summary()
    decision = await generate_query_decision("What were our monthly sales in 2025?", schema, [])
    assert decision.is_supported is True
    assert decision.is_ambiguous is False
    assert decision.chart_type == "line"
    assert decision.x_axis == "order_month"

    cols, rows, exec_time = await execute_safe_sql(decision.sql)
    assert len(rows) > 0
    assert "order_month" in cols


@pytest.mark.asyncio
async def test_ranked_customers_bar_chart():
    schema = await get_schema_summary()
    decision = await generate_query_decision("Who are our top 10 customers by spending?", schema, [])
    assert decision.is_supported is True
    assert decision.is_ambiguous is False
    assert decision.chart_type == "bar"
    assert decision.x_axis == "customer_name"

    cols, rows, exec_time = await execute_safe_sql(decision.sql)
    assert len(rows) <= 10
    assert "customer_name" in cols
    assert "total_spending_inr" in cols


@pytest.mark.asyncio
async def test_composition_percentage_pie_chart():
    schema = await get_schema_summary()
    decision = await generate_query_decision("What percentage of sales came from each region?", schema, [])
    assert decision.is_supported is True
    assert decision.is_ambiguous is False
    assert decision.chart_type in ["pie", "donut"]
    assert decision.x_axis == "region"

    cols, rows, exec_time = await execute_safe_sql(decision.sql)
    assert len(rows) > 0
    assert "percentage_share" in cols


@pytest.mark.asyncio
async def test_ambiguity_and_semantic_recency_followup():
    schema = await get_schema_summary()
    # 1. Ask ambiguous question
    decision = await generate_query_decision("Show me our best customers", schema, [])
    assert decision.is_ambiguous is True
    assert decision.clarification_question is not None
    assert "best customers" in decision.clarification_question.lower()
    assert len(decision.clarification_options) >= 3

    # 2. Select "Most recent purchase" -> Semantic check: MUST be table, not spending bar chart!
    followup_recency = await generate_query_decision(
        "Most recent purchase",
        schema,
        [
            ChatMessage(role="user", content="Show me our best customers"),
            ChatMessage(role="assistant", content=decision.clarification_question)
        ]
    )
    assert followup_recency.is_ambiguous is False
    assert followup_recency.chart_type == "table"  # Recency is rendered as table
    assert "latest_purchase_date" in followup_recency.sql

    cols, rows, _ = await execute_safe_sql(followup_recency.sql)
    assert len(rows) > 0
    assert "latest_purchase_date" in cols


@pytest.mark.asyncio
async def test_unsupported_questions():
    schema = await get_schema_summary()
    
    # Weather
    d1 = await generate_query_decision("What is today's weather forecast?", schema, [])
    assert d1.is_supported is False
    assert d1.unsupported_reason is not None
    assert d1.sql is None

    # Employee satisfaction
    d2 = await generate_query_decision("What is our employee satisfaction score?", schema, [])
    assert d2.is_supported is False
    assert d2.sql is None


@pytest.mark.asyncio
async def test_security_rejections():
    safe1, _ = validate_safe_sql("SELECT name FROM customers;")
    assert safe1 is True

    unsafe1, err1 = validate_safe_sql("DROP TABLE customers;")
    assert unsafe1 is False

    unsafe2, err2 = validate_safe_sql("DELETE FROM orders WHERE id = 1;")
    assert unsafe2 is False

    unsafe3, err3 = validate_safe_sql("UPDATE products SET price = 0;")
    assert unsafe3 is False


@pytest.mark.asyncio
async def test_robust_chart_fallback():
    # If no numeric column exists across multiple rows, must fallback to table
    cols = ["customer_name", "city", "state"]
    rows = [
        {"customer_name": "Aarav", "city": "Mumbai", "state": "Maharashtra"},
        {"customer_name": "Priya", "city": "Ahmedabad", "state": "Gujarat"}
    ]
    
    chart, x, y = resolve_robust_chart_type("bar", "customer_name", "total_spent", cols, rows, False)
    assert chart == "table"
