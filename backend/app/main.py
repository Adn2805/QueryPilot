from contextlib import asynccontextmanager
import logging
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import QueryRequest, QueryResponse, KPIMetric, DrillDownRequest, FilterCondition, DrillDownOption
from app.database import get_db_pool, close_db_pool, get_schema_summary, execute_safe_sql
from app.llm import generate_query_decision, get_drilldown_options_for_dimension, build_drilldown_query_decision

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("querypilot.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: test connection
    logger.info("Connecting to PostgreSQL database...")
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            val = await conn.fetchval("SELECT 1;")
            logger.info(f"Database connection verified: {val}")
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
    
    yield

    # Shutdown
    logger.info("Closing database connections...")
    await close_db_pool()


app = FastAPI(
    title="QueryPilot - Text-to-SQL AI Assistant",
    version="2.1.0",
    description="Intelligent Text-to-SQL engine with Pydantic structured outputs, dynamic KPI cards, and ambiguity clarification.",
    lifespan=lifespan
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_kpi_metrics(columns: List[str], rows: List[Dict[str, Any]], currency_symbol: str) -> List[KPIMetric]:
    """
    Extracts structured KPI cards when query returns headline aggregate figures (1-2 rows).
    """
    if not rows or len(rows) > 3:
        return []

    kpi_list: List[KPIMetric] = []
    row = rows[0]

    for col in columns:
        val = row.get(col)
        if val is None:
            continue

        label = col.replace("_inr", "").replace("_", " ").title()
        
        if isinstance(val, (int, float)):
            col_lower = col.lower()
            if any(k in col_lower for k in ["revenue", "amount", "price", "spending", "spent", "value", "aov"]):
                formatted = f"{currency_symbol}{val:,.2f}"
                unit = "INR"
            elif any(k in col_lower for k in ["percent", "share", "pct", "rate"]):
                formatted = f"{val:,.2f}%"
                unit = "Percentage"
            elif any(k in col_lower for k in ["count", "orders", "customers", "quantity", "units", "items", "total"]):
                formatted = f"{int(val):,}"
                unit = "Count"
            else:
                formatted = f"{val:,.2f}" if isinstance(val, float) else f"{val:,}"
                unit = None

            kpi_list.append(KPIMetric(
                label=label,
                value=val,
                formatted=formatted,
                unit=unit
            ))

    return kpi_list


def resolve_robust_chart_type(
    suggested_chart: str,
    x_axis: str | None,
    y_axis: str | None,
    columns: List[str],
    rows: List[Dict[str, Any]],
    is_kpi: bool
) -> tuple[str, str | None, str | None]:
    """
    Validates that chart columns exist and data is numeric.
    Gracefully falls back to 'table' or 'kpi' if chart constraints are not met.
    """
    if not rows:
        return "table", None, None

    # Single-row aggregate -> KPI
    if len(rows) == 1 and len(columns) <= 4:
        return "kpi", None, None

    if suggested_chart == "kpi" or is_kpi:
        return "kpi", None, None

    if suggested_chart not in ["bar", "line", "pie", "donut"]:
        return "table", None, None

    # Verify column existence
    x_col = x_axis if (x_axis and x_axis in columns) else columns[0]
    
    # Find valid numeric column for y_axis
    num_cols = [c for c in columns if len(rows) > 0 and isinstance(rows[0].get(c), (int, float))]
    
    if y_axis and y_axis in num_cols:
        y_col = y_axis
    elif num_cols:
        y_col = num_cols[0] if num_cols[0] != x_col else (num_cols[1] if len(num_cols) > 1 else num_cols[0])
    else:
        # No numeric data found -> Fallback to table
        return "table", None, None

    return suggested_chart, x_col, y_col


@app.get("/api/health")
async def health_check():
    """Returns system status, active LLM provider, and database health."""
    db_ok = False
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1;")
            db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "database_connected": db_ok,
        "llm_provider": settings.LLM_PROVIDER,
        "currency_symbol": settings.DEFAULT_CURRENCY_SYMBOL
    }


@app.get("/api/schema")
async def get_schema():
    """Returns database schema summary for UI display and context."""
    try:
        summary = await get_schema_summary()
        return {"schema_markdown": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sample-queries")
async def get_sample_queries():
    """Comprehensive sample queries covering all major enterprise analytics patterns."""
    return [
        {
            "category": "Profitability Analysis",
            "query": "Show net profit margin by brand",
            "type": "sql"
        },
        {
            "category": "Marketing Attribution ROI",
            "query": "Compare revenue by customer acquisition channel",
            "type": "sql"
        },
        {
            "category": "Logistics & Carrier SLA",
            "query": "Show average delivery days by shipping carrier",
            "type": "sql"
        },
        {
            "category": "Inventory Stockout Risk",
            "query": "Which products are below their reorder level?",
            "type": "sql"
        },
        {
            "category": "Customer Segment Analysis",
            "query": "Show revenue contribution by customer segment",
            "type": "sql"
        },
        {
            "category": "Geographic Composition",
            "query": "What percentage of sales came from each region?",
            "type": "sql"
        },
        {
            "category": "Ambiguity Clarification",
            "query": "Show me our best customers",
            "type": "clarification"
        },
        {
            "category": "Security Protection",
            "query": "DROP TABLE customers;",
            "type": "security"
        },
        {
            "category": "Unsupported Domain",
            "query": "What is today's weather forecast?",
            "type": "unsupported"
        }
    ]


@app.post("/api/query", response_model=QueryResponse)
async def process_natural_language_query(req: QueryRequest):
    """
    End-to-End Query Pipeline:
    1. Schema Introspection
    2. Pydantic Structured Output Decision
    3. Handles: Unsupported, Ambiguous Clarification, or Safe SQL Execution
    4. Auto-resolves presentation format (KPI cards, Bar/Line/Pie charts, Data Table)
    """
    user_msg = req.message.strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Query message cannot be empty.")

    try:
        # Step 1: Introspect database schema
        schema_context = await get_schema_summary()

        # Step 2: Call LLM with Pydantic Structured Output
        decision = await generate_query_decision(
            question=user_msg,
            schema_context=schema_context,
            history=req.history
        )

        # Case A: Unsupported / Out of domain
        if not decision.is_supported:
            return QueryResponse(
                type="unsupported",
                question=user_msg,
                is_supported=False,
                unsupported_reason=decision.unsupported_reason or "Question cannot be answered from the current database schema.",
                explanation=decision.explanation
            )

        # Case B: Ambiguous query -> return clarification
        if decision.is_ambiguous:
            return QueryResponse(
                type="clarification",
                question=user_msg,
                is_supported=True,
                is_ambiguous=True,
                clarification_question=decision.clarification_question,
                clarification_options=decision.clarification_options,
                explanation=decision.explanation
            )

        # Case C: Clear query -> execute generated SQL
        if not decision.sql:
            return QueryResponse(
                type="error",
                question=user_msg,
                error="The query engine did not produce a SQL statement.",
                explanation=decision.explanation
            )

        try:
            columns, rows, exec_time = await execute_safe_sql(decision.sql)
            
            # Extract KPI metrics if applicable
            kpis = extract_kpi_metrics(columns, rows, settings.DEFAULT_CURRENCY_SYMBOL)
            is_kpi_result = bool(kpis) and (decision.is_kpi or len(rows) == 1)

            # Robust chart type validation
            final_chart, final_x, final_y = resolve_robust_chart_type(
                suggested_chart=decision.chart_type,
                x_axis=decision.x_axis,
                y_axis=decision.y_axis,
                columns=columns,
                rows=rows,
                is_kpi=is_kpi_result
            )

            # Dynamic drilldown options for the returned dimension
            drilldown_opts = get_drilldown_options_for_dimension(
                dimension_name=decision.dimension_name,
                current_metric=decision.metric_name,
                active_filters=[]
            )

            metadata = {
                "row_count": len(rows),
                "execution_time_ms": exec_time,
                "metric": decision.metric_name or "value",
                "dimension": decision.dimension_name or "category",
                "is_kpi": is_kpi_result
            }

            return QueryResponse(
                type="sql_result",
                question=user_msg,
                is_supported=True,
                is_ambiguous=False,
                sql=decision.sql,
                explanation=decision.explanation,
                columns=columns,
                rows=rows,
                row_count=len(rows),
                execution_time_ms=exec_time,
                is_kpi=is_kpi_result,
                kpi_metrics=kpis,
                chart_type=final_chart,
                x_axis=final_x,
                y_axis=final_y,
                metric_name=decision.metric_name,
                dimension_name=decision.dimension_name,
                drilldown_options=drilldown_opts,
                active_filters=[],
                query_metadata=metadata
            )
        except ValueError as val_err:
            # Blocked unsafe query or validation failure
            return QueryResponse(
                type="error",
                question=user_msg,
                sql=decision.sql,
                explanation=decision.explanation,
                error=f"Security / Validation Notice: {str(val_err)}"
            )
        except Exception as db_err:
            # SQL Execution error
            return QueryResponse(
                type="error",
                question=user_msg,
                sql=decision.sql,
                explanation=decision.explanation,
                error=f"Database Execution Error: {str(db_err)}"
            )

    except Exception as e:
        logger.exception("Error in query pipeline")
        return QueryResponse(
            type="error",
            question=user_msg,
            error=f"Pipeline Error: {str(e)}"
        )


@app.post("/api/drill-down", response_model=QueryResponse)
async def process_drill_down_query(req: DrillDownRequest):
    """
    Executes an application-controlled structured drill-down.
    Preserves metric + active filters + generates safe PostgreSQL SELECT query.
    """
    try:
        # Step 1: Build structured query decision
        decision = build_drilldown_query_decision(req)

        if not decision.sql:
            return QueryResponse(
                type="error",
                question=req.drilldown_label or req.target_action,
                error="Failed to generate SQL for this drill-down combination.",
                explanation=decision.explanation
            )

        # Step 2: Validate and execute SQL
        columns, rows, exec_time = await execute_safe_sql(decision.sql)

        # Step 3: Format KPIs / robust chart
        kpis = extract_kpi_metrics(columns, rows, settings.DEFAULT_CURRENCY_SYMBOL)
        is_kpi_result = bool(kpis) and (decision.is_kpi or len(rows) == 1)

        final_chart, final_x, final_y = resolve_robust_chart_type(
            suggested_chart=decision.chart_type,
            x_axis=decision.x_axis,
            y_axis=decision.y_axis,
            columns=columns,
            rows=rows,
            is_kpi=is_kpi_result
        )

        # Step 4: Next-level drilldown options
        next_drilldown_options = get_drilldown_options_for_dimension(
            decision.dimension_name,
            decision.metric_name,
            req.active_filters
        )

        metadata = {
            "row_count": len(rows),
            "execution_time_ms": exec_time,
            "metric": decision.metric_name or "value",
            "dimension": decision.dimension_name or "category",
            "is_kpi": is_kpi_result,
            "is_drill_down": True
        }

        display_question = req.drilldown_label or f"Drill-down: {req.target_dimension or req.target_action}"

        return QueryResponse(
            type="sql_result",
            question=display_question,
            is_supported=True,
            is_ambiguous=False,
            sql=decision.sql,
            explanation=decision.explanation,
            columns=columns,
            rows=rows,
            row_count=len(rows),
            execution_time_ms=exec_time,
            is_kpi=is_kpi_result,
            kpi_metrics=kpis,
            chart_type=final_chart,
            x_axis=final_x,
            y_axis=final_y,
            metric_name=decision.metric_name,
            dimension_name=decision.dimension_name,
            drilldown_options=next_drilldown_options,
            active_filters=req.active_filters,
            query_metadata=metadata
        )

    except ValueError as val_err:
        return QueryResponse(
            type="error",
            question=req.drilldown_label or req.target_action,
            error=f"Security / Validation Notice: {str(val_err)}"
        )
    except Exception as e:
        logger.exception("Drill-down execution error")
        return QueryResponse(
            type="error",
            question=req.drilldown_label or req.target_action,
            error=f"Drill-down Execution Error: {str(e)}"
        )
