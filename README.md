# QueryPilot ⚡
### Conversational Text-to-SQL Analytics Engine with Interactive Drill-Downs

QueryPilot is a lightweight Text-to-SQL engine built with **Python**, **FastAPI**, **PostgreSQL**, **Pydantic Structured Outputs**, and **React**. It translates natural-language business questions into validated PostgreSQL SELECT queries, resolves ambiguity interactively, and supports multi-turn exploratory analytics through **"Follow the Number"** drill-downs.

---

## 🌟 Why QueryPilot?

Traditional Text-to-SQL assistants frequently fail in real-world analytical scenarios because they:
1. **Guess intent when questions are ambiguous** (e.g., answering *"Who are our top customers?"* without knowing if the user means revenue, order volume, or recent activity).
2. **Break on multi-table schema relationships** (failing to navigate joins across orders, shipments, order items, and products).
3. **Lack exploratory follow-ups**, requiring users to repeatedly type new prompts instead of interactively exploring data dimensions.
4. **Risk database corruption** by lacking strict read-only execution guardrails.

QueryPilot solves this with a transparent, schema-aware pipeline:
- **Dynamic Schema Introspection**: Reads catalog metadata, data types, foreign key relationships, and metric aliases into prompts.
- **Ambiguity Clarification Engine**: Flags underspecified questions and presents structured metric choices before generating SQL.
- **Follow the Number (Interactive Drill-Down)**: Allows users to click on chart elements, KPI cards, or data table cells to drill into underlying dimensions (e.g., *Customer Segment* $\to$ *Region* $\to$ *Monthly Trend*) while preserving active filter stacks.
- **Deterministic SQL Guardrails**: Enforces read-only SELECT execution, blocks mutating DDL/DML, caps row limits, and prevents SQL injection.
- **Adaptive Visual Resolver**: Automatically routes query outputs to KPI metric cards, ranked bar charts, time-series line charts, composition donut charts, or searchable data tables.

---

## 📊 Relational Database Architecture

The system operates on an Indian e-commerce relational schema comprising **6 relational tables**, **88 attributes**, and **6,929 relational records** spanning over 2.5 years of transaction data (February 2023 – September 2025):

```
 customers (150 rows) ────────┐
 (demographics, age_group,    │
  acquisition_channel, LTV)   │
                              ▼
                           orders (1,500 rows) ────────► shipments (1,500 rows)
                           (subtotal, discounts,         (BlueDart/Delhivery/FedEx,
                            tax, coupon_code)             dispatch/delivery dates)
                              │
                              ▼
 products (32 rows) ────► order_items (3,737 rows)
 (brand, cost_price,      (quantities, unit costs,
  margin_amt, stock/min)   item profit, return status)
      ▲
      │
 sellers (10 rows)
 (rating, commission, tier)
```

| Table | Records | Attributes | Key Columns |
| :--- | :---: | :---: | :--- |
| **`customers`** | 150 | 20 | `id`, `full_name`, `email`, `city`, `state`, `region`, `customer_segment`, `acquisition_channel`, `lifetime_value_tier` |
| **`sellers`** | 10 | 9 | `id`, `seller_name`, `business_name`, `city`, `state`, `rating`, `commission_rate`, `fulfillment_type` |
| **`products`** | 32 | 18 | `id`, `sku`, `product_name`, `brand`, `primary_category`, `cost_price`, `selling_price`, `stock_quantity`, `reorder_level` |
| **`orders`** | 1,500 | 22 | `id`, `order_number`, `customer_id`, `seller_id`, `order_date`, `status`, `payment_method`, `total_amount`, `delivery_days` |
| **`order_items`** | 3,737 | 11 | `id`, `order_id`, `product_id`, `quantity`, `unit_cost_price`, `unit_selling_price`, `total_item_revenue`, `item_profit_margin` |
| **`shipments`** | 1,500 | 8 | `id`, `order_id`, `carrier`, `tracking_number`, `status`, `dispatch_date`, `delivery_date`, `shipping_cost_inr` |

---

## 🏗️ System Architecture & Workflow

```
User Query / Clarification / Drill-Down Action
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. FastAPI REST Layer (`POST /api/query`, `/api/drill-down`)│
│ Receives message + schema catalog + active filter stack     │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Pydantic Structured Output Engine (`QueryDecision`)      │
│ • If Ambiguous ──▶ Returns clarification question & options │
│ • If Supported ──▶ Generates parameterized PostgreSQL query │
│ • If Unrelated ──▶ Explains unsupported domain boundaries   │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. SQL Safety & Execution Guardrail                         │
│ • Disallows mutating DDL/DML & multi-statement queries      │
│ • Executes on PostgreSQL with connection pooling & timeouts │
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Single-Page React Studio (`App.tsx`)                     │
│ • Renders KPI Headline Cards, Recharts, or Data Table       │
│ • Manages interactive Breadcrumb Trail & DrillDownMenu      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2 (Structured Outputs), `asyncpg`, `uvicorn`, `pytest`, `pytest-asyncio`.
- **Database**: PostgreSQL 16 (relational schema with indexes and foreign keys), Redis 7 (optional cache layer).
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Recharts, Lucide Icons, Axios.
- **DevOps**: Docker, Docker Compose, Multi-stage builds.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Docker and Docker Compose (or local PostgreSQL 16)

### 1. Start PostgreSQL with Docker
```bash
# Start the database container
docker compose up -d postgres
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Optionally provide your `OPENAI_API_KEY` in `.env`. If no key is set, QueryPilot automatically falls back to its deterministic rule engine).*

### 3. Seed Database & Start Backend
```bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Seed the 6 enterprise tables (6,929 rows)
python backend/seed.py

# Start FastAPI backend (port 8000)
uvicorn app.main:app --app-dir backend --reload --port 8000
```

### 4. Start React Frontend
```bash
cd frontend
npm install
npm run dev -- --port 3000
```
Open **http://localhost:3000** in your browser.

---

## 🧪 Verified Analytical Scenarios

| Analysis Type | Example Natural Language Query | Presentation Format | Underlying SQL Mechanism |
| :--- | :--- | :--- | :--- |
| **Executive KPI** | *"What is our overall net profit and total revenue?"* | KPI Headline Cards | `SUM(item_profit_margin)`, `SUM(total_amount)` |
| **Brand Profitability** | *"Which brand generated the highest net profit margin?"* | Ranked Bar Chart | Multi-table join on `products` and `order_items` |
| **Channel Attribution** | *"Show revenue and order volume by acquisition channel"* | Composition Donut Chart | Group by `customers.acquisition_channel` |
| **Logistics SLA** | *"Compare delivery transit days and shipping cost across carriers"* | Comparison Bar Chart | `AVG(delivery_date - dispatch_date)` on `shipments` |
| **Inventory Alert** | *"Show products with stock below reorder level"* | Data Table | Filter `stock_quantity <= reorder_level` |
| **Ambiguity Resolution** | *"Who are our top customers?"* | Interactive Option Cards | Prompts user to pick Spending vs. Orders vs. AOV vs. Recency |
| **Security Guardrail** | *"DROP TABLE customers;"* | Security Warning | AST & regex safety layer rejects non-SELECT queries |

---

## 🔍 "Follow the Number" Interactive Drill-Down Demo Flow

QueryPilot enables multi-turn exploratory analytics without writing queries:

1. **Ask**: *"What is our profit by customer segment?"*
   - QueryPilot returns KPI and bar chart breakdown (`Enterprise: ₹2.41M`, `SMB: ₹1.83M`, `VIP: ₹1.12M`, `Consumer: ₹0.76M`).
2. **Drill Down**: Click **Enterprise** $\to$ Select **"Break down by Region"**.
   - QueryPilot executes a parameterized query filtering `customer_segment = 'Enterprise'`, grouping by `region`.
3. **Consecutive Drill Down**: Click **North** $\to$ Select **"Show Monthly Trend"**.
   - QueryPilot preserves all active filters (`customer_segment = 'Enterprise' AND region = 'North'`) and plots a 24-month line chart.
4. **Reversible Navigation**: Click any step in the **Breadcrumb Trail** or **Root** to restore the previous analytical state instantly.

---

## 🎯 Automated Testing

Run the full test suite of **31 automated pytest cases**:
```bash
$env:PYTHONPATH="backend"; pytest backend/tests/ -v
```

Test suites cover:
- `test_api_endpoints.py`: REST endpoint responses, error states, and schema introspection.
- `test_drill_down.py`: Multi-level filter persistence, breadcrumb restoration, and injection sanitization.
- `test_enterprise_big_data.py`: Multi-table joins across all 6 relational tables.
- `test_simplified_pipeline.py`: Ambiguity detection and SQL safety checks.
- `test_upgraded_engine.py`: Adaptive visual routing, KPI formatting, and time-series line resolvers.

---

## 📁 Repository Structure

```
querypilot/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application & REST routing
│   │   ├── config.py        # Environment configuration
│   │   ├── database.py      # PostgreSQL pool & schema reader
│   │   ├── llm.py           # Structured output caller & drill-down generator
│   │   └── models.py        # Pydantic schemas (QueryDecision, DrillDownRequest)
│   ├── seed.py              # Database seeding script (6,929 records)
│   ├── requirements.txt     # Python dependencies
│   └── tests/               # 31 automated pytest cases
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Dual-panel analytics studio & state manager
│   │   ├── components/      # Breadcrumbs, DrillDownMenu, Charts, Tables, SQL Viewer
│   │   └── types/           # TypeScript interfaces
│   └── package.json
├── docker-compose.yml       # Container definitions for PostgreSQL and Redis
├── .env.example             # Clean environment variable template
└── README.md
```
