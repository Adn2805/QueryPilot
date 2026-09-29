import pytest
from app.database import get_schema_summary, validate_safe_sql, execute_safe_sql
from app.llm import generate_query_decision
from app.models import ChatMessage
from app.main import extract_kpi_metrics, resolve_robust_chart_type


@pytest.mark.asyncio
async def test_enterprise_schema_summary():
    summary = await get_schema_summary()
    # Check all 6 enterprise tables exist
    for tbl in ["customers", "sellers", "products", "orders", "order_items", "shipments"]:
        assert tbl in summary
    assert "Profitability" in summary
    assert "Logistics" in summary
    assert "Marketing" in summary


@pytest.mark.asyncio
async def test_profit_margin_by_brand_query():
    schema = await get_schema_summary()
    decision = await generate_query_decision("Show net profit margin by brand", schema, [])
    assert decision.is_supported is True
    assert decision.is_ambiguous is False
    assert decision.chart_type == "bar"
    assert decision.x_axis == "brand"
    assert decision.sql is not None

    cols, rows, exec_time = await execute_safe_sql(decision.sql)
    assert len(rows) > 0
    assert "brand" in cols
    assert "total_profit_inr" in cols
    # Ensure profit values are calculated
    assert rows[0]["total_profit_inr"] > 0
    assert exec_time < 200  # Sub-200ms execution on indexed dataset


@pytest.mark.asyncio
async def test_marketing_channel_roi_query():
    schema = await get_schema_summary()
    decision = await generate_query_decision("Compare revenue by customer acquisition channel", schema, [])
    assert decision.is_supported is True
    assert decision.is_ambiguous is False
    assert decision.chart_type == "pie"
    assert decision.x_axis == "acquisition_channel"

    cols, rows, exec_time = await execute_safe_sql(decision.sql)
    assert len(rows) > 0
    assert "acquisition_channel" in cols
    assert "channel_revenue_inr" in cols


@pytest.mark.asyncio
async def test_carrier_logistics_query():
    schema = await get_schema_summary()
    decision = await generate_query_decision("Show average delivery days by shipping carrier", schema, [])
    assert decision.is_supported is True
    assert decision.is_ambiguous is False
    assert decision.chart_type == "bar"
    assert decision.x_axis == "carrier"

    cols, rows, exec_time = await execute_safe_sql(decision.sql)
    assert len(rows) > 0
    assert "carrier" in cols
    assert "avg_delivery_days" in cols


@pytest.mark.asyncio
async def test_inventory_stockout_risk_query():
    schema = await get_schema_summary()
    decision = await generate_query_decision("Which products are below their reorder level?", schema, [])
    assert decision.is_supported is True
    assert decision.is_ambiguous is False
    assert decision.chart_type == "table"

    cols, rows, exec_time = await execute_safe_sql(decision.sql)
    assert "sku" in cols
    assert "stock_quantity" in cols
    assert "reorder_level" in cols


@pytest.mark.asyncio
async def test_customer_segment_revenue():
    schema = await get_schema_summary()
    decision = await generate_query_decision("Show revenue contribution by customer segment", schema, [])
    assert decision.is_supported is True
    assert decision.is_ambiguous is False
    assert decision.chart_type == "bar"
    assert decision.x_axis == "customer_segment"

    cols, rows, exec_time = await execute_safe_sql(decision.sql)
    assert len(rows) > 0
    assert "customer_segment" in cols
    assert "segment_revenue_inr" in cols


@pytest.mark.asyncio
async def test_overall_profit_kpi():
    schema = await get_schema_summary()
    decision = await generate_query_decision("What is our overall net profit margin?", schema, [])
    assert decision.is_supported is True
    assert decision.is_ambiguous is False
    assert decision.is_kpi is True

    cols, rows, exec_time = await execute_safe_sql(decision.sql)
    assert len(rows) == 1
    assert "total_net_profit_inr" in cols

    kpis = extract_kpi_metrics(cols, rows, "₹")
    assert len(kpis) >= 1
    assert "₹" in kpis[0].formatted
