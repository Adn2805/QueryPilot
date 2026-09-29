from typing import List, Optional, Any, Dict, Literal
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class QueryRequest(BaseModel):
    message: str = Field(..., description="The user's natural language question or clarification response")
    history: List[ChatMessage] = Field(default_factory=list, description="Prior conversation history for context")
    conversation_id: Optional[str] = Field(None, description="Optional conversation identifier for isolation")


class KPIMetric(BaseModel):
    label: str = Field(..., description="Display label for the metric card (e.g. Total Revenue, Order Count)")
    value: Any = Field(..., description="Raw or numeric value")
    formatted: str = Field(..., description="Human-formatted string with currency/commas (e.g. ₹6,659,939.00)")
    unit: Optional[str] = Field(None, description="Unit or subtitle (e.g. INR, orders, items)")


class QueryDecision(BaseModel):
    """
    Structured Output schema returned directly by the LLM.
    Guarantees deterministic, strongly-typed classification and SQL generation.
    """
    is_supported: bool = Field(
        default=True,
        description="False if the question asks for data not present in the database (e.g. weather, employee satisfaction, future predictions)"
    )
    unsupported_reason: Optional[str] = Field(
        None,
        description="Explanation of why this information is unavailable in the database"
    )
    is_ambiguous: bool = Field(
        default=False,
        description="True if the user's query lacks clarity, metrics, date ranges, or definitions needing clarification"
    )
    clarification_question: Optional[str] = Field(
        None,
        description="The follow-up question to ask the user if is_ambiguous is True"
    )
    clarification_options: List[str] = Field(
        default_factory=list,
        description="2 to 4 recommended choices for the user to resolve ambiguity"
    )
    sql: Optional[str] = Field(
        None,
        description="PostgreSQL SELECT query to execute if is_ambiguous is False and is_supported is True"
    )
    explanation: str = Field(
        ...,
        description="Brief, clear explanation of what was calculated or why clarification/unsupported state was triggered"
    )
    metric_name: Optional[str] = Field(
        None,
        description="Name of the primary metric being computed (e.g. total_revenue, order_count, total_spent)"
    )
    dimension_name: Optional[str] = Field(
        None,
        description="Name of the primary grouping dimension (e.g. category, state, month, customer)"
    )
    is_kpi: bool = Field(
        default=False,
        description="True if the result is a single-value or headline summary suitable for KPI metric cards"
    )
    chart_type: Literal["table", "bar", "line", "pie", "donut", "kpi"] = Field(
        default="table",
        description="Recommended visual presentation for the query result"
    )
    x_axis: Optional[str] = Field(
        None,
        description="Column name to use for chart X axis / category"
    )
    y_axis: Optional[str] = Field(
        None,
        description="Column name to use for chart Y axis / numeric value"
    )


class FilterCondition(BaseModel):
    dimension: str = Field(..., description="Column/dimension name being filtered, e.g. customer_segment, region, brand, primary_category")
    value: str = Field(..., description="Value to filter by, e.g. Enterprise, North, Electronics, Apple")
    display_label: Optional[str] = Field(None, description="Human readable label, e.g. Segment: Enterprise")


class DrillDownOption(BaseModel):
    action_id: str = Field(..., description="Unique identifier for the action, e.g. breakdown_region, breakdown_category, monthly_trend, top_customers")
    label: str = Field(..., description="User-facing title, e.g. Break down by Region")
    target_dimension: str = Field(..., description="Target dimension column name, e.g. region, brand, primary_category, order_month")
    icon: Optional[str] = Field("bar", description="Icon hint: bar, line, pie, table, users, tag, map")
    description: Optional[str] = Field(None, description="Brief explanation of the analytical cut")


class DrillDownRequest(BaseModel):
    """
    Application-controlled structured drill-down request.
    Transfers structured context (filters + target dimension + metric) safely.
    """
    target_action: str = Field(..., description="Action ID selected by user")
    target_dimension: Optional[str] = Field(None, description="Target dimension to group by")
    current_metric: Optional[str] = Field(None, description="Metric being preserved (e.g. profit, revenue, aov, orders)")
    active_filters: List[FilterCondition] = Field(default_factory=list, description="Stack of active filters")
    original_query: Optional[str] = Field(None, description="Original question for conversational grounding")
    drilldown_label: Optional[str] = Field(None, description="Breadcrumb label for this drill-down step")
    history: List[ChatMessage] = Field(default_factory=list, description="Prior conversational context")


class QueryResponse(BaseModel):
    type: Literal["clarification", "sql_result", "unsupported", "error"]
    question: str
    is_supported: bool = True
    unsupported_reason: Optional[str] = None
    is_ambiguous: bool = False
    clarification_question: Optional[str] = None
    clarification_options: List[str] = []
    sql: Optional[str] = None
    explanation: Optional[str] = None
    columns: List[str] = []
    rows: List[Dict[str, Any]] = []
    row_count: int = 0
    execution_time_ms: float = 0.0
    is_kpi: bool = False
    kpi_metrics: List[KPIMetric] = []
    chart_type: Literal["table", "bar", "line", "pie", "donut", "kpi"] = "table"
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    metric_name: Optional[str] = None
    dimension_name: Optional[str] = None
    drilldown_options: List[DrillDownOption] = []
    active_filters: List[FilterCondition] = []
    query_metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
