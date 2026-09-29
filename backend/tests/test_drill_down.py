import pytest
from app.models import DrillDownRequest, FilterCondition
from app.llm import get_drilldown_options_for_dimension, build_drilldown_query_decision
from app.database import execute_safe_sql, validate_safe_sql


@pytest.mark.asyncio
async def test_drilldown_options_generation():
    # Options for customer_segment
    opts = get_drilldown_options_for_dimension("customer_segment", "total_profit_inr", [])
    assert len(opts) > 0
    target_dims = [o.target_dimension for o in opts]
    assert "region" in target_dims
    assert "primary_category" in target_dims
    assert "order_month" in target_dims
    # Should not offer customer_segment again
    assert "customer_segment" not in target_dims


@pytest.mark.asyncio
async def test_flow_1_profit_segment_to_region_to_north_to_monthly_trend():
    """
    Test Flow 1:
    Profit by Segment -> Enterprise -> Region -> North -> Monthly Trend
    """
    # Step 1: Drill into Enterprise -> Break down by Region
    req1 = DrillDownRequest(
        target_action="breakdown_region",
        target_dimension="region",
        current_metric="profit",
        active_filters=[
            FilterCondition(dimension="customer_segment", value="Enterprise", display_label="Segment: Enterprise")
        ],
        original_query="What is our profit by customer segment?",
        drilldown_label="Enterprise → Break down by Region"
    )
    d1 = build_drilldown_query_decision(req1)
    assert d1.is_supported is True
    assert "c.customer_segment = 'Enterprise'" in d1.sql
    assert "c.region" in d1.sql
    assert "item_profit_margin" in d1.sql
    assert d1.chart_type == "bar"
    assert d1.x_axis == "region"

    cols1, rows1, _ = await execute_safe_sql(d1.sql)
    assert len(rows1) > 0
    assert "region" in cols1
    assert "total_profit_inr" in cols1

    # Step 2: From Region: North -> Show Monthly Trend (2 active filters!)
    req2 = DrillDownRequest(
        target_action="monthly_trend",
        target_dimension="order_month",
        current_metric="profit",
        active_filters=[
            FilterCondition(dimension="customer_segment", value="Enterprise", display_label="Segment: Enterprise"),
            FilterCondition(dimension="region", value="North", display_label="Region: North")
        ],
        original_query="What is our profit by customer segment?",
        drilldown_label="North → Show Monthly Trend"
    )
    d2 = build_drilldown_query_decision(req2)
    assert "c.customer_segment = 'Enterprise'" in d2.sql
    assert "c.region = 'North'" in d2.sql
    assert "order_month" in d2.sql
    assert "item_profit_margin" in d2.sql
    assert d2.chart_type == "line"

    cols2, rows2, _ = await execute_safe_sql(d2.sql)
    assert len(rows2) > 0
    assert "order_month" in cols2
    assert "total_profit_inr" in cols2


@pytest.mark.asyncio
async def test_flow_2_revenue_category_to_electronics_to_brand_to_apple():
    """
    Test Flow 2:
    Revenue by Category -> Electronics -> Brand -> Apple
    """
    # Step 1: Category: Electronics -> Brand
    req1 = DrillDownRequest(
        target_action="breakdown_brand",
        target_dimension="brand",
        current_metric="revenue",
        active_filters=[
            FilterCondition(dimension="primary_category", value="Electronics", display_label="Category: Electronics")
        ],
        original_query="Show revenue by category",
        drilldown_label="Electronics → Break down by Brand"
    )
    d1 = build_drilldown_query_decision(req1)
    assert "Electronics" in d1.sql
    assert "p.brand" in d1.sql
    assert d1.chart_type == "bar"
    assert d1.x_axis == "brand"

    cols1, rows1, _ = await execute_safe_sql(d1.sql)
    assert len(rows1) > 0
    assert "brand" in cols1
    assert "total_revenue_inr" in cols1

    # Step 2: From Brand: Apple -> Top Products
    req2 = DrillDownRequest(
        target_action="top_products",
        target_dimension="top_products",
        current_metric="revenue",
        active_filters=[
            FilterCondition(dimension="primary_category", value="Electronics", display_label="Category: Electronics"),
            FilterCondition(dimension="brand", value="Apple", display_label="Brand: Apple")
        ],
        original_query="Show revenue by category",
        drilldown_label="Apple → Top Products"
    )
    d2 = build_drilldown_query_decision(req2)
    assert "Electronics" in d2.sql
    assert "p.brand = 'Apple'" in d2.sql
    assert "p.product_name" in d2.sql

    cols2, rows2, _ = await execute_safe_sql(d2.sql)
    assert len(rows2) > 0
    assert "product_name" in cols2


@pytest.mark.asyncio
async def test_flow_3_channel_to_google_ads_to_customer_segment():
    """
    Test Flow 3:
    Acquisition Channel -> Google Ads -> Customer Segment
    """
    req = DrillDownRequest(
        target_action="breakdown_segment",
        target_dimension="customer_segment",
        current_metric="revenue",
        active_filters=[
            FilterCondition(dimension="acquisition_channel", value="Google Ads", display_label="Channel: Google Ads")
        ],
        original_query="Show revenue by customer acquisition channel",
        drilldown_label="Google Ads → Break down by Customer Segment"
    )
    d = build_drilldown_query_decision(req)
    assert "c.acquisition_channel = 'Google Ads'" in d.sql
    assert "c.customer_segment" in d.sql
    assert d.chart_type == "bar"
    assert d.x_axis == "customer_segment"

    cols, rows, _ = await execute_safe_sql(d.sql)
    assert len(rows) > 0
    assert "customer_segment" in cols
    assert "total_revenue_inr" in cols


@pytest.mark.asyncio
async def test_drilldown_sql_safety_and_escaping():
    # Malicious injection attempt in filter value
    req = DrillDownRequest(
        target_action="breakdown_region",
        target_dimension="region",
        current_metric="revenue",
        active_filters=[
            FilterCondition(dimension="customer_segment", value="Enterprise'; DROP TABLE customers; --")
        ]
    )
    d = build_drilldown_query_decision(req)
    # The value should be safely escaped with '' and not break query syntax
    assert "DROP TABLE" not in d.sql or "''" in d.sql
    is_safe, _ = validate_safe_sql(d.sql)
    assert is_safe is True
