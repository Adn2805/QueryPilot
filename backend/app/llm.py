import json
import logging
import re
from typing import List
import openai
from app.config import settings
from app.models import QueryDecision, ChatMessage, FilterCondition, DrillDownOption, DrillDownRequest

logger = logging.getLogger("querypilot.llm")

SYSTEM_PROMPT_TEMPLATE = """You are QueryPilot, an expert AI Enterprise SQL Data Analyst for PostgreSQL.
Your goal is to convert natural language business questions into precise, read-only PostgreSQL SELECT queries grounded in the database schema.

{schema_context}

### RULES & CONSTRAINTS:

1. **Unsupported / Out-of-Domain Detection**:
   - If the question asks for data NOT present in the database (e.g. weather, employee HR surveys, future stock prices, server telemetry, general trivia):
     * Set `is_supported = False`
     * Set `unsupported_reason` explaining that the required information is not stored in the database.
     * Set `sql = None`

2. **Ambiguity Detection & Clarification**:
   - If the request is ambiguous, underspecified, or has multiple valid business definitions (e.g. "Who are our best customers?", "Top performing products", "Recent performance"):
     * Set `is_ambiguous = True`
     * Set `clarification_question` to a polite, direct question.
     * Set `clarification_options` with 2 to 4 distinct, actionable choices (e.g. ["By total revenue spent", "By number of orders placed", "By profit margin generated", "By most recent purchase"]).
     * Set `sql = None`.

3. **Enterprise PostgreSQL SQL Generation**:
   - Generate standard, valid PostgreSQL `SELECT` SQL.
   - Use table joins properly (`orders.customer_id = customers.id`, `order_items.order_id = orders.id`, `order_items.product_id = products.id`, `shipments.order_id = orders.id`, `orders.seller_id = sellers.id`).
   - Use appropriate aggregations (`SUM`, `AVG`, `COUNT`, `ROUND`, `MIN`, `MAX`) and column aliases (`total_revenue_inr`, `net_profit_inr`, `avg_delivery_days`).
   - Only produce read-only statements (SELECT / WITH). Never produce DDL/DML.

4. **Semantic Presentation Alignment**:
   - Single aggregate metrics (Total Revenue, Net Profit, Order Count, AOV) -> `chart_type = "kpi"`, `is_kpi = True`.
   - Categorical rankings (Revenue by Brand, Margin by Category, Carrier Delivery Speed) -> `chart_type = "bar"`.
   - Time-series trends (Monthly sales, Quarterly trends) -> `chart_type = "line"`.
   - Composition shares (Percentage share by state, share by channel, payment breakdown) -> `chart_type = "pie"`.
   - Complex multi-attribute records, contact lists, or stockout alerts -> `chart_type = "table"`.
"""


def _demo_rule_fallback(question: str, history: List[ChatMessage]) -> QueryDecision:
    """
    Enterprise-grade deterministic NLP & rule engine for big multi-attribute data queries.
    Handles profitability, marketing channels, logistics, inventory health, aggregations, ambiguity, and follow-ups.
    """
    q_lower = question.lower().strip()
    history_text = " ".join([h.content.lower() for h in history])

    # 1. Unsafe / Destructive check
    if any(re.search(rf"\b{w}\b", q_lower) for w in ["drop", "delete", "truncate", "update", "insert", "alter", "grant", "revoke"]):
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql="SELECT 'Blocked: DDL/DML operation detected' AS security_alert;",
            explanation="Mutating operations (DROP, DELETE, UPDATE, INSERT, ALTER) are strictly blocked for security.",
            chart_type="table"
        )

    # 2. Unsupported / Out-of-domain questions
    unsupported_keywords = [
        "weather", "temperature", "forecast", "employee", "salary", "satisfaction",
        "churn prediction", "predict churn", "stock price", "nasdaq", "president", "minister", "traffic",
        "server cpu", "crypto", "bitcoin"
    ]
    if any(k in q_lower for k in unsupported_keywords):
        return QueryDecision(
            is_supported=False,
            unsupported_reason="This question asks for information not present in the enterprise database (which contains customers, sellers, products, orders, order_items, and shipments).",
            is_ambiguous=False,
            explanation="External domain information (weather, HR employee surveys, server telemetry, stock market forecasts) is outside the current database schema.",
            chart_type="table"
        )

    # 3. Clarification Follow-ups from History
    is_cust_ctx = "customer" in q_lower or "customer" in history_text or "best customer" in history_text or "top customer" in history_text

    # Clarification: Highest Spending
    if "highest total spending" in q_lower or "by total revenue" in q_lower or ("spending" in q_lower and is_cust_ctx) or q_lower in ["customer spendings", "customer spending", "customer spend"]:
        year_filter = "AND EXTRACT(YEAR FROM o.order_date) = 2025" if ("2025" in q_lower or "2025" in history_text) else ""
        limit_val = 5 if ("5" in q_lower or "top 5" in history_text) else 10
        order_dir = "ASC" if ("lowest" in q_lower or "bottom" in q_lower) else "DESC"

        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql=f"""
            SELECT c.full_name AS customer_name, c.customer_segment, c.city, c.state, SUM(o.total_amount) AS total_spending_inr, COUNT(o.id) AS total_orders
            FROM customers c
            JOIN orders o ON c.id = o.customer_id
            WHERE o.status IN ('Delivered', 'Completed') {year_filter}
            GROUP BY c.id, c.full_name, c.customer_segment, c.city, c.state
            ORDER BY total_spending_inr {order_dir}
            LIMIT {limit_val};
            """.strip(),
            explanation=f"Top {limit_val} customers ranked by total completed order spending in INR{' for 2025' if year_filter else ''}.",
            metric_name="total_spending_inr",
            dimension_name="customer_name",
            chart_type="bar",
            x_axis="customer_name",
            y_axis="total_spending_inr"
        )

    # Clarification: Most Orders
    if "most order" in q_lower or "by number of order" in q_lower or ("order count" in q_lower and is_cust_ctx):
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql="""
            SELECT c.full_name AS customer_name, c.customer_segment, c.city, COUNT(o.id) AS order_count, SUM(o.total_amount) AS total_spent_inr
            FROM customers c
            JOIN orders o ON c.id = o.customer_id
            GROUP BY c.id, c.full_name, c.customer_segment, c.city
            ORDER BY order_count DESC
            LIMIT 10;
            """.strip(),
            explanation="Top 10 customers ranked by total order frequency/count.",
            metric_name="order_count",
            dimension_name="customer_name",
            chart_type="bar",
            x_axis="customer_name",
            y_axis="order_count"
        )

    # Clarification: Most Recent Purchase (Recency -> Table!)
    if "most recent purchase" in q_lower or "latest purchase" in q_lower:
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql="""
            SELECT c.full_name AS customer_name, c.customer_segment, c.city, c.state, MAX(o.order_date) AS latest_purchase_date, COUNT(o.id) AS total_orders, SUM(o.total_amount) AS total_spent_inr
            FROM customers c
            JOIN orders o ON c.id = o.customer_id
            GROUP BY c.id, c.full_name, c.customer_segment, c.city, c.state
            ORDER BY latest_purchase_date DESC
            LIMIT 10;
            """.strip(),
            explanation="Customers ranked by their most recent order date.",
            metric_name="latest_purchase_date",
            dimension_name="customer_name",
            chart_type="table"
        )

    # 4. Ambiguity Detection
    if ("best customer" in q_lower or "top customer" in q_lower) and not any(k in q_lower for k in ["revenue", "order", "spend", "aov", "profit", "margin", "city", "state"]):
        return QueryDecision(
            is_supported=True,
            is_ambiguous=True,
            clarification_question="How should we define 'best customers'?",
            clarification_options=[
                "Highest total spending",
                "Most orders placed",
                "Highest average order value",
                "Most recent purchase"
            ],
            explanation="Customer rankings can be evaluated by gross revenue, transaction count, average basket size, or recency."
        )

    if ("best product" in q_lower or "top product" in q_lower or "popular product" in q_lower) and not any(k in q_lower for k in ["revenue", "unit", "quantity", "margin", "profit", "rating"]):
        return QueryDecision(
            is_supported=True,
            is_ambiguous=True,
            clarification_question="How would you like to measure top products?",
            clarification_options=[
                "By total revenue generated",
                "By total units sold",
                "By net profit margin",
                "By customer rating"
            ],
            explanation="Product performance can be measured by sales revenue, unit volume, profit margin, or customer ratings."
        )

    # 5. Average Revenue / AOV (Average Order Value)
    if "average" in q_lower or "avg" in q_lower or "mean" in q_lower or "aov" in q_lower:
        if any(k in q_lower for k in ["revenue", "order", "sale", "spending", "amount", "value", "price"]) or q_lower in ["average revenue", "avg revenue", "aov", "average order value"]:
            return QueryDecision(
                is_supported=True,
                is_ambiguous=False,
                sql="""
                SELECT 
                    ROUND(AVG(total_amount), 2) AS avg_order_value_inr,
                    SUM(total_amount) AS total_revenue_inr,
                    COUNT(id) AS total_orders
                FROM orders
                WHERE status IN ('Delivered', 'Completed');
                """.strip(),
                explanation="Calculated average order revenue (AOV), total enterprise revenue, and completed order count.",
                metric_name="avg_order_value_inr",
                is_kpi=True,
                chart_type="kpi"
            )

    # 6. Profitability & Financial Margins
    if "profit" in q_lower or "margin" in q_lower:
        if "brand" in q_lower:
            return QueryDecision(
                is_supported=True,
                is_ambiguous=False,
                sql="""
                SELECT p.brand, SUM(oi.total_item_revenue) AS total_revenue_inr, SUM(oi.item_profit_margin) AS total_profit_inr,
                       ROUND(100.0 * SUM(oi.item_profit_margin) / NULLIF(SUM(oi.total_item_revenue), 0), 2) AS profit_margin_pct
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                GROUP BY p.brand
                ORDER BY total_profit_inr DESC
                LIMIT 10;
                """.strip(),
                explanation="Total revenue, net profit margin in INR, and profit margin percentage by brand.",
                metric_name="total_profit_inr",
                dimension_name="brand",
                chart_type="bar",
                x_axis="brand",
                y_axis="total_profit_inr"
            )

        if "category" in q_lower:
            return QueryDecision(
                is_supported=True,
                is_ambiguous=False,
                sql="""
                SELECT p.primary_category AS category, SUM(oi.total_item_revenue) AS total_revenue_inr, SUM(oi.item_profit_margin) AS total_profit_inr,
                       ROUND(100.0 * SUM(oi.item_profit_margin) / NULLIF(SUM(oi.total_item_revenue), 0), 2) AS profit_margin_pct
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                GROUP BY p.primary_category
                ORDER BY total_profit_inr DESC;
                """.strip(),
                explanation="Profitability and margin analysis grouped by primary product category.",
                metric_name="total_profit_inr",
                dimension_name="category",
                chart_type="bar",
                x_axis="category",
                y_axis="total_profit_inr"
            )

        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql="""
            SELECT 
                SUM(total_item_revenue) AS total_revenue_inr,
                SUM(item_profit_margin) AS total_net_profit_inr,
                ROUND(100.0 * SUM(item_profit_margin) / NULLIF(SUM(total_item_revenue), 0), 2) AS overall_profit_margin_pct
            FROM order_items
            WHERE return_status = 'None';
            """.strip(),
            explanation="Overall enterprise net profit margin and margin percentage.",
            metric_name="total_net_profit_inr",
            is_kpi=True,
            chart_type="kpi"
        )

    # 7. Marketing Acquisition Channel & ROI
    if "channel" in q_lower or "acquisition" in q_lower or "marketing" in q_lower:
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql="""
            SELECT c.acquisition_channel, COUNT(DISTINCT c.id) AS total_customers, COUNT(o.id) AS total_orders,
                   SUM(o.total_amount) AS channel_revenue_inr,
                   ROUND(AVG(o.total_amount), 2) AS avg_order_value_inr,
                   ROUND(100.0 * SUM(o.total_amount) / SUM(SUM(o.total_amount)) OVER (), 2) AS revenue_share_pct
            FROM customers c
            JOIN orders o ON c.id = o.customer_id
            WHERE o.status IN ('Delivered', 'Completed')
            GROUP BY c.acquisition_channel
            ORDER BY channel_revenue_inr DESC;
            """.strip(),
            explanation="Customer acquisition channel performance, order volume, revenue in INR, and percentage share.",
            metric_name="channel_revenue_inr",
            dimension_name="acquisition_channel",
            chart_type="pie",
            x_axis="acquisition_channel",
            y_axis="channel_revenue_inr"
        )

    # 8. Logistics & Carrier Performance (SLA Delivery Speed)
    if "carrier" in q_lower or "delivery" in q_lower or "shipping" in q_lower or "logistics" in q_lower or "shipment" in q_lower:
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql="""
            SELECT s.carrier, COUNT(s.id) AS total_shipments,
                   ROUND(AVG(o.delivery_days), 2) AS avg_delivery_days,
                   SUM(s.shipping_cost_inr) AS total_shipping_cost_inr,
                   COUNT(CASE WHEN o.status = 'Returned' THEN 1 END) AS returned_orders
            FROM shipments s
            JOIN orders o ON s.order_id = o.id
            GROUP BY s.carrier
            ORDER BY total_shipments DESC;
            """.strip(),
            explanation="Logistics carrier performance comparing shipment volume, average delivery turnaround days, and return counts.",
            metric_name="avg_delivery_days",
            dimension_name="carrier",
            chart_type="bar",
            x_axis="carrier",
            y_axis="avg_delivery_days"
        )

    # 9. Inventory & Stockout Risk
    if "stock" in q_lower or "inventory" in q_lower or "reorder" in q_lower:
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql="""
            SELECT sku, product_name, brand, primary_category AS category, stock_quantity, reorder_level,
                   (reorder_level - stock_quantity) AS units_needed
            FROM products
            WHERE stock_quantity <= reorder_level
            ORDER BY stock_quantity ASC;
            """.strip(),
            explanation="Inventory stockout risk report listing SKUs at or below their safety reorder threshold.",
            metric_name="stock_quantity",
            dimension_name="product_name",
            chart_type="table"
        )

    # 10. Customer Segments Analysis
    if "segment" in q_lower or "tier" in q_lower or "vip" in q_lower:
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql="""
            SELECT c.customer_segment, COUNT(DISTINCT c.id) AS customer_count, COUNT(o.id) AS total_orders,
                   SUM(o.total_amount) AS segment_revenue_inr,
                   ROUND(AVG(o.total_amount), 2) AS avg_order_value_inr
            FROM customers c
            JOIN orders o ON c.id = o.customer_id
            WHERE o.status IN ('Delivered', 'Completed')
            GROUP BY c.customer_segment
            ORDER BY segment_revenue_inr DESC;
            """.strip(),
            explanation="Revenue and order contribution across customer segments (Enterprise, SMB, Consumer, VIP).",
            metric_name="segment_revenue_inr",
            dimension_name="customer_segment",
            chart_type="bar",
            x_axis="customer_segment",
            y_axis="segment_revenue_inr"
        )

    # 11. Regional & State Breakdown
    if "region" in q_lower or "state" in q_lower:
        if "percentage" in q_lower or "share" in q_lower or "%" in q_lower:
            return QueryDecision(
                is_supported=True,
                is_ambiguous=False,
                sql="""
                WITH region_sales AS (
                    SELECT c.region, SUM(o.total_amount) AS region_revenue
                    FROM orders o
                    JOIN customers c ON o.customer_id = c.id
                    WHERE o.status IN ('Delivered', 'Completed')
                    GROUP BY c.region
                )
                SELECT region, region_revenue AS revenue_inr,
                       ROUND(100.0 * region_revenue / SUM(region_revenue) OVER (), 2) AS percentage_share
                FROM region_sales
                ORDER BY percentage_share DESC;
                """.strip(),
                explanation="Percentage contribution of sales revenue by geographic region (North, South, East, West, Central).",
                metric_name="percentage_share",
                dimension_name="region",
                chart_type="pie",
                x_axis="region",
                y_axis="percentage_share"
            )

        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql="""
            SELECT c.state, c.region, SUM(o.total_amount) AS total_revenue_inr, COUNT(o.id) AS total_orders, COUNT(DISTINCT c.id) AS customer_count
            FROM customers c
            JOIN orders o ON c.id = o.customer_id
            WHERE o.status IN ('Delivered', 'Completed')
            GROUP BY c.state, c.region
            ORDER BY total_revenue_inr DESC
            LIMIT 10;
            """.strip(),
            explanation="Top 10 states by completed transaction revenue and customer count.",
            metric_name="total_revenue_inr",
            dimension_name="state",
            chart_type="bar",
            x_axis="state",
            y_axis="total_revenue_inr"
        )

    # 12. Category Breakdown
    if "category" in q_lower or "categories" in q_lower:
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql="""
            SELECT p.primary_category AS category, SUM(oi.total_item_revenue) AS total_revenue_inr, SUM(oi.quantity) AS total_units_sold,
                   SUM(oi.item_profit_margin) AS total_profit_inr
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            JOIN orders o ON oi.order_id = o.id
            WHERE o.status IN ('Delivered', 'Completed')
            GROUP BY p.primary_category
            ORDER BY total_revenue_inr DESC;
            """.strip(),
            explanation="Revenue, units sold, and profit margin aggregated by primary product category.",
            metric_name="total_revenue_inr",
            dimension_name="category",
            chart_type="bar",
            x_axis="category",
            y_axis="total_revenue_inr"
        )

    # 13. Top Products
    if "product" in q_lower and ("revenue" in q_lower or "top" in q_lower or "sold" in q_lower or "selling" in q_lower):
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql="""
            SELECT p.product_name, p.brand, p.primary_category AS category, SUM(oi.total_item_revenue) AS total_revenue_inr, SUM(oi.quantity) AS total_units_sold
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            JOIN orders o ON oi.order_id = o.id
            WHERE o.status IN ('Delivered', 'Completed')
            GROUP BY p.id, p.product_name, p.brand, p.primary_category
            ORDER BY total_revenue_inr DESC
            LIMIT 10;
            """.strip(),
            explanation="Top 10 product SKUs ranked by total sales revenue in INR.",
            metric_name="total_revenue_inr",
            dimension_name="product_name",
            chart_type="bar",
            x_axis="product_name",
            y_axis="total_revenue_inr"
        )

    # 14. Payment Methods
    if "payment" in q_lower or "upi" in q_lower or "credit card" in q_lower:
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql="""
            SELECT payment_method, COUNT(id) AS order_count, SUM(total_amount) AS total_revenue_inr,
                   ROUND(100.0 * COUNT(id) / SUM(COUNT(id)) OVER (), 2) AS order_percentage
            FROM orders
            GROUP BY payment_method
            ORDER BY order_count DESC;
            """.strip(),
            explanation="Transaction volume and payment method distribution across all orders.",
            metric_name="order_count",
            dimension_name="payment_method",
            chart_type="pie",
            x_axis="payment_method",
            y_axis="order_count"
        )

    # 15. Headline KPI Aggregations (Total Revenue, AOV, Order Count)
    if (q_lower in ["revenue", "sales", "total sales", "total revenue", "turnover", "overall revenue"]) or (("total revenue" in q_lower or "overall revenue" in q_lower or "how much revenue" in q_lower or "total sales" in q_lower or "gross revenue" in q_lower) and not any(k in q_lower for k in ["category", "state", "region", "month", "by", "each", "trend", "brand", "channel", "carrier", "segment"])):
        year_filter = ""
        year_title = "across all years"
        if "2025" in q_lower:
            year_filter = "AND EXTRACT(YEAR FROM order_date) = 2025"
            year_title = "in 2025"
        elif "2024" in q_lower:
            year_filter = "AND EXTRACT(YEAR FROM order_date) = 2024"
            year_title = "in 2024"
        elif "2023" in q_lower:
            year_filter = "AND EXTRACT(YEAR FROM order_date) = 2023"
            year_title = "in 2023"

        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql=f"""
            SELECT 
                SUM(total_amount) AS total_revenue_inr,
                COUNT(id) AS total_orders,
                ROUND(AVG(total_amount), 2) AS avg_order_value_inr
            FROM orders
            WHERE status IN ('Delivered', 'Completed') {year_filter};
            """.strip(),
            explanation=f"Overall enterprise total revenue, total orders, and average order value (AOV) {year_title}.",
            metric_name="total_revenue_inr",
            is_kpi=True,
            chart_type="kpi"
        )

    # 16. Monthly Sales Trends (Time-series Line Chart)
    if "month" in q_lower or "trend" in q_lower or "monthly" in q_lower or "quarter" in q_lower or ("2025" in q_lower and "revenue" not in q_lower):
        year_filter = ""
        year_title = "across all years"
        if "2025" in q_lower:
            year_filter = "AND EXTRACT(YEAR FROM order_date) = 2025"
            year_title = "in 2025"
        elif "2024" in q_lower:
            year_filter = "AND EXTRACT(YEAR FROM order_date) = 2024"
            year_title = "in 2024"
        elif "2023" in q_lower:
            year_filter = "AND EXTRACT(YEAR FROM order_date) = 2023"
            year_title = "in 2023"

        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql=f"""
            SELECT TO_CHAR(order_date, 'YYYY-MM') AS order_month, SUM(total_amount) AS monthly_revenue_inr, COUNT(id) AS order_count
            FROM orders
            WHERE status IN ('Delivered', 'Completed') {year_filter}
            GROUP BY TO_CHAR(order_date, 'YYYY-MM')
            ORDER BY order_month ASC;
            """.strip(),
            explanation=f"Monthly sales revenue and order volume trend {year_title}.",
            metric_name="monthly_revenue_inr",
            dimension_name="order_month",
            chart_type="line",
            x_axis="order_month",
            y_axis="monthly_revenue_inr"
        )

    # 17. Entity Lists (Customers, Products, Sellers, Orders)
    if q_lower in ["customers", "all customers", "show customers", "customer list", "customer profiles", "user list"] or ("customer" in q_lower and any(k in q_lower for k in ["list", "show", "all", "directory"])):
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql="""
            SELECT c.customer_code, c.full_name, c.email, c.city, c.state, c.customer_segment, c.acquisition_channel, c.lifetime_value_tier,
                   COUNT(o.id) AS total_orders, COALESCE(SUM(o.total_amount), 0) AS lifetime_spending_inr
            FROM customers c
            LEFT JOIN orders o ON c.id = o.customer_id AND o.status IN ('Delivered', 'Completed')
            GROUP BY c.id, c.customer_code, c.full_name, c.email, c.city, c.state, c.customer_segment, c.acquisition_channel, c.lifetime_value_tier
            ORDER BY lifetime_spending_inr DESC
            LIMIT 20;
            """.strip(),
            explanation="Listing enterprise customer profiles with lifetime spending, total orders, and segment tier.",
            chart_type="table"
        )

    if q_lower in ["products", "all products", "show products", "product list", "catalog", "inventory list"] or ("product" in q_lower and any(k in q_lower for k in ["list", "catalog", "inventory", "all", "show"])):
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql="""
            SELECT sku, product_name, brand, primary_category AS category, cost_price, selling_price, margin_amount, stock_quantity, reorder_level, rating
            FROM products
            ORDER BY stock_quantity ASC
            LIMIT 20;
            """.strip(),
            explanation="Listing product catalog with SKU, brand, pricing, margins, and stock levels.",
            chart_type="table"
        )

    if q_lower in ["sellers", "all sellers", "seller list", "partners", "merchants"]:
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql="""
            SELECT seller_code, seller_name, business_name, city, state, rating, commission_rate, fulfillment_type
            FROM sellers
            ORDER BY rating DESC;
            """.strip(),
            explanation="Listing marketplace sellers with ratings, commission rates, and fulfillment tiers.",
            chart_type="table"
        )

    # Default fallback: Recent orders list
    return QueryDecision(
        is_supported=True,
        is_ambiguous=False,
        sql="""
        SELECT o.order_number, c.full_name AS customer_name, c.city, o.order_date, o.status, o.payment_method, o.total_amount AS amount_inr
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        ORDER BY o.order_date DESC
        LIMIT 15;
        """.strip(),
        explanation="Listing the 15 most recent orders with customer names, fulfillment status, and transaction totals.",
        chart_type="table"
    )


async def generate_query_decision(
    question: str,
    schema_context: str,
    history: List[ChatMessage]
) -> QueryDecision:
    """
    Calls configured LLM with Pydantic Structured Outputs (QueryDecision)
    or falls back to enterprise deterministic rules.
    """
    provider = settings.LLM_PROVIDER.lower()
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(schema_context=schema_context)

    # 1. OpenAI with beta parse
    if provider == "openai" and settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "sk-your-key-here":
        try:
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            messages = [{"role": "system", "content": system_prompt}]
            for msg in history[-8:]:
                messages.append({"role": msg.role, "content": msg.content})
            messages.append({"role": "user", "content": question})

            response = await client.beta.chat.completions.parse(
                model=settings.OPENAI_MODEL,
                messages=messages,
                response_format=QueryDecision,
                temperature=0.0
            )
            parsed = response.choices[0].message.parsed
            if parsed:
                return parsed
        except Exception as e:
            logger.warning(f"OpenAI call failed ({e}), falling back to enterprise deterministic engine.")

    # 2. Groq endpoint
    elif provider == "groq" and settings.GROQ_API_KEY:
        try:
            client = openai.AsyncOpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url="https://api.groq.com/openai/v1"
            )
            
            messages = [{"role": "system", "content": system_prompt}]
            for msg in history[-8:]:
                messages.append({"role": msg.role, "content": msg.content})
            messages.append({"role": "user", "content": question})

            response = await client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.0
            )
            content = response.choices[0].message.content
            if content:
                data = json.loads(content)
                return QueryDecision(**data)
        except Exception as e:
            logger.warning(f"Groq call failed ({e}), falling back to enterprise deterministic engine.")

    # 3. Deterministic NLP / Fallback Engine
    return _demo_rule_fallback(question, history)


def get_drilldown_options_for_dimension(
    dimension_name: str | None,
    current_metric: str | None,
    active_filters: List[FilterCondition]
) -> List[DrillDownOption]:
    """
    Returns dynamically computed schema-valid drill-down options based on
    current dimension, metric, and active filter conditions.
    """
    active_dims = {f.dimension.lower() for f in active_filters}
    current_dim = (dimension_name or "").lower()

    catalog_options = [
        ("breakdown_region", "Break down by Region", "region", "map", "Analyze regional distribution (North, South, East, West)"),
        ("breakdown_category", "Break down by Category", "primary_category", "tag", "Split across primary product categories"),
        ("breakdown_brand", "Break down by Brand", "brand", "bar", "Compare performance across top brands"),
        ("breakdown_segment", "Break down by Customer Segment", "customer_segment", "users", "Analyze by Enterprise, VIP, SMB, Consumer"),
        ("breakdown_channel", "Analyze Acquisition Channel", "acquisition_channel", "pie", "Attribution across Google Ads, Meta, Organic"),
        ("monthly_trend", "Show Monthly Trend", "order_month", "line", "Time-series trend across months"),
        ("top_customers", "Show Top Customers", "top_customers", "users", "Top customers ranked by contribution"),
        ("top_products", "Show Top Products", "top_products", "tag", "Top product SKUs ranked by contribution"),
        ("breakdown_state", "Break down by State", "state", "map", "State-level geographic distribution"),
        ("breakdown_carrier", "Break down by Carrier", "carrier", "bar", "Logistics carrier breakdown"),
        ("breakdown_payment", "Break down by Payment Method", "payment_method", "pie", "Payment method distribution"),
        ("view_orders", "View Underlying Orders", "orders", "table", "Inspect individual underlying order records"),
    ]

    options: List[DrillDownOption] = []
    for action_id, label, target_dim, icon, desc in catalog_options:
        # Don't offer the exact same dimension we are currently on or already filtered by
        if target_dim in active_dims or target_dim == current_dim or (target_dim == "primary_category" and ("category" in active_dims or current_dim in ["primary_category", "category"])):
            continue
        
        options.append(DrillDownOption(
            action_id=action_id,
            label=label,
            target_dimension=target_dim,
            icon=icon,
            description=desc
        ))

    return options[:6]


def build_drilldown_query_decision(req: DrillDownRequest) -> QueryDecision:
    """
    Application-controlled SQL generation for structured drill-down requests.
    Guarantees that all active filters and metric definitions are preserved across consecutive drilldowns.
    """
    target_dim = (req.target_dimension or "region").lower()
    metric_str = (req.current_metric or "revenue").lower()
    orig_query = (req.original_query or "").lower()

    # 1. Determine Metric Aggregations
    is_profit = any(k in metric_str or k in orig_query for k in ["profit", "margin"])
    is_aov = any(k in metric_str or k in orig_query for k in ["aov", "average", "avg"])
    is_delivery = any(k in metric_str or k in orig_query for k in ["carrier", "delivery", "transit", "shipping"])
    is_units = any(k in metric_str or k in orig_query for k in ["unit", "quantity", "sold"])

    if is_profit:
        metric_expr = """SUM(oi.item_profit_margin) AS total_profit_inr,
               SUM(oi.total_item_revenue) AS total_revenue_inr,
               ROUND(100.0 * SUM(oi.item_profit_margin) / NULLIF(SUM(oi.total_item_revenue), 0), 2) AS profit_margin_pct"""
        order_col = "total_profit_inr"
        y_axis = "total_profit_inr"
        metric_label = "net profit margin in INR"
    elif is_aov:
        metric_expr = """ROUND(AVG(o.total_amount), 2) AS avg_order_value_inr,
               SUM(o.total_amount) AS total_revenue_inr,
               COUNT(DISTINCT o.id) AS total_orders"""
        order_col = "avg_order_value_inr"
        y_axis = "avg_order_value_inr"
        metric_label = "average order value (AOV) in INR"
    elif is_delivery:
        metric_expr = """ROUND(AVG(o.delivery_days), 2) AS avg_delivery_days,
               COUNT(DISTINCT s.id) AS total_shipments,
               SUM(s.shipping_cost_inr) AS total_shipping_cost_inr"""
        order_col = "avg_delivery_days"
        y_axis = "avg_delivery_days"
        metric_label = "average delivery transit days"
    elif is_units:
        metric_expr = """SUM(oi.quantity) AS total_units_sold,
               SUM(oi.total_item_revenue) AS total_revenue_inr"""
        order_col = "total_units_sold"
        y_axis = "total_units_sold"
        metric_label = "total units sold"
    else:
        # Default Revenue
        metric_expr = """SUM(oi.total_item_revenue) AS total_revenue_inr,
               COUNT(DISTINCT o.id) AS total_orders,
               SUM(oi.quantity) AS total_units_sold"""
        order_col = "total_revenue_inr"
        y_axis = "total_revenue_inr"
        metric_label = "total revenue in INR"

    # 2. Build WHERE Filter Stack
    where_clauses = ["o.status IN ('Delivered', 'Completed')"]
    filter_descriptions = []

    for f in req.active_filters:
        dim = f.dimension.lower()
        # Sanitize against SQL injection attempts (strip semicolons & DDL/DML keywords)
        clean_val = re.sub(r"(?i)\b(DROP|DELETE|TRUNCATE|UPDATE|INSERT|ALTER|GRANT|REVOKE|EXEC|EXECUTE)\b", "", f.value)
        clean_val = clean_val.replace(";", "").replace("--", "").strip()
        val = clean_val.replace("'", "''")
        filter_descriptions.append(f"{f.dimension} = '{f.value}'")

        if dim in ["customer_segment", "segment"]:
            where_clauses.append(f"c.customer_segment = '{val}'")
        elif dim in ["region"]:
            where_clauses.append(f"c.region = '{val}'")
        elif dim in ["state"]:
            where_clauses.append(f"c.state = '{val}'")
        elif dim in ["city"]:
            where_clauses.append(f"c.city = '{val}'")
        elif dim in ["acquisition_channel", "channel"]:
            where_clauses.append(f"c.acquisition_channel = '{val}'")
        elif dim in ["primary_category", "category"]:
            where_clauses.append(f"(p.primary_category = '{val}' OR p.category = '{val}')")
        elif dim in ["brand"]:
            where_clauses.append(f"p.brand = '{val}'")
        elif dim in ["product_name", "product"]:
            where_clauses.append(f"p.product_name = '{val}'")
        elif dim in ["carrier"]:
            where_clauses.append(f"s.carrier = '{val}'")
        elif dim in ["payment_method"]:
            where_clauses.append(f"o.payment_method = '{val}'")
        elif dim in ["order_month", "month"]:
            where_clauses.append(f"TO_CHAR(o.order_date, 'YYYY-MM') = '{val}'")
        elif dim in ["customer_name", "customer"]:
            where_clauses.append(f"c.full_name = '{val}'")

    where_sql = " AND ".join(where_clauses)
    filter_summary = ", ".join(filter_descriptions) if filter_descriptions else "all data"

    # 3. Construct Query by Target Dimension
    if target_dim in ["region"]:
        sql = f"""
        SELECT c.region, {metric_expr}
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN order_items oi ON oi.order_id = o.id
        LEFT JOIN products p ON oi.product_id = p.id
        LEFT JOIN shipments s ON s.order_id = o.id
        WHERE {where_sql}
        GROUP BY c.region
        ORDER BY {order_col} DESC;
        """.strip()
        explanation = f"Drill-down breakdown by geographic region for {metric_label} (Filtered by {filter_summary})."
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql=sql,
            explanation=explanation,
            metric_name=order_col,
            dimension_name="region",
            chart_type="bar",
            x_axis="region",
            y_axis=y_axis
        )

    elif target_dim in ["primary_category", "category"]:
        sql = f"""
        SELECT p.primary_category AS category, {metric_expr}
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN order_items oi ON oi.order_id = o.id
        LEFT JOIN products p ON oi.product_id = p.id
        LEFT JOIN shipments s ON s.order_id = o.id
        WHERE {where_sql}
        GROUP BY p.primary_category
        ORDER BY {order_col} DESC;
        """.strip()
        explanation = f"Drill-down breakdown by product category for {metric_label} (Filtered by {filter_summary})."
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql=sql,
            explanation=explanation,
            metric_name=order_col,
            dimension_name="category",
            chart_type="bar",
            x_axis="category",
            y_axis=y_axis
        )

    elif target_dim in ["brand"]:
        sql = f"""
        SELECT p.brand, {metric_expr}
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN order_items oi ON oi.order_id = o.id
        LEFT JOIN products p ON oi.product_id = p.id
        LEFT JOIN shipments s ON s.order_id = o.id
        WHERE {where_sql}
        GROUP BY p.brand
        ORDER BY {order_col} DESC
        LIMIT 15;
        """.strip()
        explanation = f"Drill-down breakdown by brand for {metric_label} (Filtered by {filter_summary})."
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql=sql,
            explanation=explanation,
            metric_name=order_col,
            dimension_name="brand",
            chart_type="bar",
            x_axis="brand",
            y_axis=y_axis
        )

    elif target_dim in ["customer_segment", "segment"]:
        sql = f"""
        SELECT c.customer_segment, {metric_expr}
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN order_items oi ON oi.order_id = o.id
        LEFT JOIN products p ON oi.product_id = p.id
        LEFT JOIN shipments s ON s.order_id = o.id
        WHERE {where_sql}
        GROUP BY c.customer_segment
        ORDER BY {order_col} DESC;
        """.strip()
        explanation = f"Drill-down breakdown by customer segment for {metric_label} (Filtered by {filter_summary})."
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql=sql,
            explanation=explanation,
            metric_name=order_col,
            dimension_name="customer_segment",
            chart_type="bar",
            x_axis="customer_segment",
            y_axis=y_axis
        )

    elif target_dim in ["acquisition_channel", "channel"]:
        sql = f"""
        SELECT c.acquisition_channel, {metric_expr}
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN order_items oi ON oi.order_id = o.id
        LEFT JOIN products p ON oi.product_id = p.id
        LEFT JOIN shipments s ON s.order_id = o.id
        WHERE {where_sql}
        GROUP BY c.acquisition_channel
        ORDER BY {order_col} DESC;
        """.strip()
        explanation = f"Drill-down breakdown by customer acquisition channel for {metric_label} (Filtered by {filter_summary})."
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql=sql,
            explanation=explanation,
            metric_name=order_col,
            dimension_name="acquisition_channel",
            chart_type="pie",
            x_axis="acquisition_channel",
            y_axis=y_axis
        )

    elif target_dim in ["order_month", "monthly_trend", "month"]:
        sql = f"""
        SELECT TO_CHAR(o.order_date, 'YYYY-MM') AS order_month, {metric_expr}
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN order_items oi ON oi.order_id = o.id
        LEFT JOIN products p ON oi.product_id = p.id
        LEFT JOIN shipments s ON s.order_id = o.id
        WHERE {where_sql}
        GROUP BY TO_CHAR(o.order_date, 'YYYY-MM')
        ORDER BY order_month ASC;
        """.strip()
        explanation = f"Monthly time-series trend for {metric_label} (Filtered by {filter_summary})."
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql=sql,
            explanation=explanation,
            metric_name=order_col,
            dimension_name="order_month",
            chart_type="line",
            x_axis="order_month",
            y_axis=y_axis
        )

    elif target_dim in ["top_customers", "customer_name"]:
        sql = f"""
        SELECT c.full_name AS customer_name, c.customer_segment, c.city, c.state, {metric_expr}
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN order_items oi ON oi.order_id = o.id
        LEFT JOIN products p ON oi.product_id = p.id
        LEFT JOIN shipments s ON s.order_id = o.id
        WHERE {where_sql}
        GROUP BY c.id, c.full_name, c.customer_segment, c.city, c.state
        ORDER BY {order_col} DESC
        LIMIT 10;
        """.strip()
        explanation = f"Top 10 customers ranked by {metric_label} (Filtered by {filter_summary})."
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql=sql,
            explanation=explanation,
            metric_name=order_col,
            dimension_name="customer_name",
            chart_type="bar",
            x_axis="customer_name",
            y_axis=y_axis
        )

    elif target_dim in ["top_products", "product_name"]:
        sql = f"""
        SELECT p.product_name, p.brand, p.primary_category AS category, {metric_expr}
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN order_items oi ON oi.order_id = o.id
        LEFT JOIN products p ON oi.product_id = p.id
        LEFT JOIN shipments s ON s.order_id = o.id
        WHERE {where_sql}
        GROUP BY p.id, p.product_name, p.brand, p.primary_category
        ORDER BY {order_col} DESC
        LIMIT 10;
        """.strip()
        explanation = f"Top 10 products ranked by {metric_label} (Filtered by {filter_summary})."
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql=sql,
            explanation=explanation,
            metric_name=order_col,
            dimension_name="product_name",
            chart_type="bar",
            x_axis="product_name",
            y_axis=y_axis
        )

    elif target_dim in ["state"]:
        sql = f"""
        SELECT c.state, c.region, {metric_expr}
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN order_items oi ON oi.order_id = o.id
        LEFT JOIN products p ON oi.product_id = p.id
        LEFT JOIN shipments s ON s.order_id = o.id
        WHERE {where_sql}
        GROUP BY c.state, c.region
        ORDER BY {order_col} DESC
        LIMIT 10;
        """.strip()
        explanation = f"Drill-down breakdown by state for {metric_label} (Filtered by {filter_summary})."
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql=sql,
            explanation=explanation,
            metric_name=order_col,
            dimension_name="state",
            chart_type="bar",
            x_axis="state",
            y_axis=y_axis
        )

    elif target_dim in ["carrier"]:
        sql = f"""
        SELECT s.carrier, {metric_expr}
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        LEFT JOIN order_items oi ON oi.order_id = o.id
        LEFT JOIN products p ON oi.product_id = p.id
        LEFT JOIN shipments s ON s.order_id = o.id
        WHERE {where_sql}
        GROUP BY s.carrier
        ORDER BY {order_col} DESC;
        """.strip()
        explanation = f"Drill-down breakdown by carrier for {metric_label} (Filtered by {filter_summary})."
        return QueryDecision(
            is_supported=True,
            is_ambiguous=False,
            sql=sql,
            explanation=explanation,
            metric_name=order_col,
            dimension_name="carrier",
            chart_type="bar",
            x_axis="carrier",
            y_axis=y_axis
        )

    # Fallback / View Orders
    sql = f"""
    SELECT o.order_number, c.full_name AS customer_name, c.city, o.order_date, o.status, o.payment_method, o.total_amount AS amount_inr
    FROM orders o
    JOIN customers c ON o.customer_id = c.id
    LEFT JOIN order_items oi ON oi.order_id = o.id
    LEFT JOIN products p ON oi.product_id = p.id
    LEFT JOIN shipments s ON s.order_id = o.id
    WHERE {where_sql}
    ORDER BY o.order_date DESC
    LIMIT 15;
    """.strip()
    explanation = f"Detailed order transactions (Filtered by {filter_summary})."
    return QueryDecision(
        is_supported=True,
        is_ambiguous=False,
        sql=sql,
        explanation=explanation,
        chart_type="table"
    )
