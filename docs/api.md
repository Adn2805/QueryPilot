# QueryPilot REST API Specification

Base URL: `http://localhost:8000/api/v1`

---

## 1. Authentication Endpoints

### Register User
- **Method**: `POST /auth/register`
- **Request Body**:
  ```json
  {
    "email": "analyst@example.com",
    "username": "data_analyst",
    "password": "SecurePassword123!",
    "role": "analyst"
  }
  ```
- **Response**: `201 Created`
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": {
      "id": "e4b2d184-...",
      "email": "analyst@example.com",
      "username": "data_analyst",
      "role": "analyst",
      "created_at": "2026-09-18T14:30:00Z"
    }
  }
  ```

### User Login
- **Method**: `POST /auth/login`
- **Request Body**:
  ```json
  {
    "email": "analyst@example.com",
    "password": "SecurePassword123!"
  }
  ```

---

## 2. Query Pipeline Endpoints

### Submit Natural-Language Query
- **Method**: `POST /query`
- **Request Body**:
  ```json
  {
    "message": "What is our total revenue for 2025?",
    "conversation_id": null
  }
  ```
- **Response (Success)**:
  ```json
  {
    "query_id": "a1b2c3d4-...",
    "conversation_id": "c5d6e7f8-...",
    "status": "success",
    "result": {
      "natural_explanation": "Total completed order revenue in 2025 was ₹4.82 crore across 3,410 transactions.",
      "columns": ["total_revenue", "order_count"],
      "rows": [{"total_revenue": 48200000.0, "order_count": 3410}],
      "row_count": 1,
      "visualization_type": "bar",
      "sql": "SELECT SUM(total_amount) AS total_revenue, COUNT(*) AS order_count FROM orders WHERE status = 'completed' AND EXTRACT(YEAR FROM order_date) = 2025 LIMIT 1000",
      "interpretation": "Aggregated completed order revenue during calendar year 2025",
      "tables_used": ["orders"],
      "execution_time_ms": 14.2,
      "retry_count": 0
    }
  }
  ```

- **Response (Clarification Required)**:
  ```json
  {
    "query_id": "b2c3d4e5-...",
    "conversation_id": "c5d6e7f8-...",
    "status": "clarification_needed",
    "clarification": {
      "question": "How should 'best customers' be measured?",
      "options": [
        "Highest total spending",
        "Most orders placed",
        "Highest average order value",
        "Highest profit margin"
      ]
    }
  }
  ```

### Query History
- **Method**: `GET /query/history?page=1&limit=25`
- **Response**: Paginated list of audit records.

### Export Query Results as CSV
- **Method**: `GET /query/{query_id}/export`
- **Response**: `text/csv` attachment.

---

## 3. Business Glossary Endpoints

- `GET /glossary` — List all defined terms and SQL formulas
- `POST /glossary` — Add new business metric (Admin)
- `PUT /glossary/{id}` — Update business metric (Admin)
- `DELETE /glossary/{id}` — Remove business metric (Admin)

---

## 4. Schema Endpoints

- `GET /schema/tables` — List all analytics tables and column counts
- `GET /schema/tables/{table_name}` — Detailed column types, PK, and FK definitions
- `GET /schema/relationships` — Foreign key relationship graph

---

## 5. Evaluation Endpoints

- `GET /evaluation/summary` — Latest empirical benchmark summary
- `POST /evaluation/run` — Trigger background benchmark execution
- `GET /evaluation/runs` — List history of benchmark runs
