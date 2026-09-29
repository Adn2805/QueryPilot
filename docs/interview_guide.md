# QueryPilot — Technical Interview Guide & Architecture Breakdown

Use this document to prepare for and confidently ace technical interviews (AI Engineer, Fullstack Engineer, or Backend Python roles).

---

## 1. 30-Second Elevator Pitch

> *"QueryPilot is a conversational Text-to-SQL analytics engine built with FastAPI, PostgreSQL, Pydantic Structured Outputs, and React. Most Text-to-SQL systems fail in production because they guess when queries are ambiguous (like 'show top customers') or risk running destructive SQL. QueryPilot uses LLM schema grounding with Pydantic structured output models to detect ambiguity and provide interactive clarification options. Once clarified, it validates read-only AST safety, executes on PostgreSQL, and visualizes the results with interactive charts."*

---

## 2. Architecture & Data Flow (Step-by-Step)

```
User Query ──▶ POST /api/query ──▶ Introspect DB Schema ──▶ LLM (QueryDecision)
                                                                 │
                   ┌─────────────────────────────────────────────┴────────────────┐
                   ▼                                                              ▼
             [Ambiguous]                                                       [Clear]
                   │                                                              │
         Return Clarification                                            Validate SELECT Safety
         Question + Option Chips                                                  │
                   │                                                              ▼
         User clicks option ───▶ (Re-enters pipeline with context)        Execute on PostgreSQL
                                                                                  │
                                                                                  ▼
                                                                         Return JSON to React
                                                                         (Charts + Table + SQL)
```

### Key Components:

1. **`app/database.py` (Schema Introspection & Safety)**:
   - Queries `information_schema.columns` to dynamically extract table names, column names, and data types without hardcoding.
   - Embeds relationship hints (`orders.customer_id -> customers.id`) into the prompt.
   - `validate_safe_sql()` enforces read-only operations (SELECT / CTEs only) and blocks multi-statement injections or destructive DDL/DML (`DROP`, `DELETE`, `UPDATE`, `ALTER`).

2. **`app/models.py` (Pydantic Structured Outputs)**:
   - Uses `QueryDecision` as the schema contract for the LLM response.
   - Properties: `is_ambiguous`, `clarification_question`, `clarification_options`, `sql`, `explanation`, `chart_type`, `x_axis`, `y_axis`.
   - **Why this matters**: Guarantees zero JSON parse errors and strictly separates the ambiguity path from the execution path.

3. **`app/llm.py` (Model Abstraction & Zero-Cost Support)**:
   - Supports OpenAI (`gpt-4o-mini`), Groq (`llama-3.3-70b-versatile`), and Gemini.
   - Includes a deterministic demo engine so the system can be demonstrated anywhere offline without API keys.

4. **`app/main.py` (FastAPI Endpoints)**:
   - Clean async route `POST /api/query` orchestrating schema retrieval, model evaluation, database execution, and error formatting.

5. **`frontend/src/App.tsx` (Single-Page Workspace)**:
   - Dual-panel layout: Left side handles the multi-turn conversational chat and clarification option chips; Right side renders interactive Recharts (Bar/Line/Pie), syntax-highlighted SQL, and the data table.

---

## 3. Common Technical Interview Questions & Answers

### Q1: Why did you use Pydantic Structured Outputs instead of standard prompt string parsing?
**Answer**: 
*Standard LLM prompts often return unstructured markdown code fences (```sql ... ```) or malformed JSON that requires brittle regex parsing. By leveraging Pydantic structured outputs (`response_format=QueryDecision`), the LLM adheres to an exact JSON Schema at decoding time. This guarantees type safety, eliminates JSON parsing exceptions, and forces the model to categorize the output as either ambiguous or executable SQL.*

---

### Q2: How do you handle conversational multi-turn context (e.g. follow-ups)?
**Answer**:
*The frontend sends the recent conversation history with every request. In `app/llm.py`, prior user queries and assistant clarification questions are passed directly into the LLM messages list. When a user clicks a clarification chip (e.g., "By total revenue spent"), the LLM sees the original query ("Who are our top customers?") and the clarification context, enabling it to generate the exact SQL query.*

---

### Q3: How do you prevent SQL injection and destructive queries?
**Answer**:
*We enforce a defense-in-depth security approach:*
1. *Prompt constraints instruct the LLM to only produce SELECT queries.*
2. *Application-level regex/AST validation (`validate_safe_sql`) ensures queries start with SELECT/WITH and rejects any DDL/DML keywords (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `TRUNCATE`, `ALTER`) and multi-query semicolon chaining.*
3. *Row capping: If the LLM omits a `LIMIT` clause, the database helper automatically injects `LIMIT 100` to prevent memory exhaustion and UI freezing.*
4. *PostgreSQL user permissions: In production, the database user connection string uses a dedicated read-only role (`GRANT SELECT ON ALL TABLES`).*

---

### Q4: Why PostgreSQL and asyncpg instead of an ORM like SQLAlchemy or Django ORM?
**Answer**:
*For a Text-to-SQL system, we are executing dynamically generated SQL queries directly against the database rather than mapping Python domain objects. `asyncpg` is the fastest asynchronous PostgreSQL driver in Python, offering native connection pooling and async event-loop integration with FastAPI with minimal overhead.*

---

### Q5: How does the system determine which chart type to render?
**Answer**:
*The `QueryDecision` model includes `chart_type` (bar, line, pie, table), `x_axis`, and `y_axis`. The LLM selects the visual format based on the query structure:*
- *Categorical aggregations (e.g., Revenue by Category) ➔ **Bar Chart***
- *Time-series trends (e.g., Monthly Sales) ➔ **Line Chart***
- *Proportions / distributions with few categories ➔ **Pie Chart***
- *Detailed entity records ➔ **Data Table***
