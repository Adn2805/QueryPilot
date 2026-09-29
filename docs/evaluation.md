# QueryPilot Evaluation Methodology & Benchmark

## 1. Zero-Fabrication Guarantee

> **CRITICAL POLICY**: QueryPilot never fabricates accuracy numbers, latencies, or security percentages. The evaluation dashboard displays "Evaluation pending" until a reproducible benchmark run executes against live PostgreSQL data.

---

## 2. Benchmark Dataset Structure

The benchmark suite includes 220 queries across 10 distinct operational categories:

| Category | Description | Target Evaluation Focus |
| :--- | :--- | :--- |
| **Simple Aggregation** | `COUNT`, `SUM`, `AVG` across single tables | Base Text-to-SQL generation accuracy |
| **Filtering** | `WHERE` clauses with numeric, string, and status conditions | Predicate accuracy and parameter binding |
| **Aggregation & GROUP BY** | Grouped metrics (e.g. sales by state or payment method) | `GROUP BY` column consistency |
| **Ranking** | Top-N queries, highest/lowest orders | `ORDER BY` clause and `LIMIT` syntax |
| **Multi-Table Joins** | Queries requiring 2-4 table relationships | Foreign key path resolution |
| **Time-Based Analytics** | Date truncations, yearly comparisons, monthly trends | Date formatting and timestamp filters |
| **Ambiguous Business Queries** | Vague phrases ("best customers", "recent performance") | Clarification engine trigger precision |
| **Multi-Turn Refinements** | Follow-up query modifications ("Only for 2025") | Context manager merge effectiveness |
| **Unsupported Domain Queries** | Predictive ML / external weather queries | Graceful unsupported rejection |
| **Unsafe Queries** | Destructive DDL / DML commands (`DROP`, `DELETE`) | 100% security blocking rate |

---

## 3. Empirical Metric Definitions

The automated metric calculator (`app/evaluation/calculator.py`) calculates the following empirical measurements:

1. **SQL Execution Accuracy**:
   $$\text{Accuracy} = \frac{\text{Valid Analytical Queries with Successful Execution}}{\text{Total Valid Analytical Queries}} \times 100$$

2. **Clarification Trigger Accuracy**:
   $$\text{Clarification Accuracy} = \frac{\text{Ambiguous Queries Correctly Prompted for Clarification}}{\text{Total Ambiguous Queries}} \times 100$$

3. **Unsafe Query Blocking Rate**:
   $$\text{Security Blocking Rate} = \frac{\text{Unsafe Queries Rejected by AST / Intent}}{\text{Total Unsafe Queries}} \times 100$$

4. **SQL Self-Repair Success Rate**:
   $$\text{Repair Success Rate} = \frac{\text{Failed Queries Corrected Within } \le 3 \text{ Retries}}{\text{Total Failed Execution Attempts}} \times 100$$

5. **Latency Telemetry**:
   - **Average Response Latency**: Mean end-to-end processing time
   - **Median Latency (P50)**: 50th percentile response latency
   - **P95 Latency**: 95th percentile response latency

---

## 4. Architecture Comparison: Baseline vs. QueryPilot

```
Baseline (Naive Text-to-SQL):
User ──▶ Raw LLM ──▶ SQL ──▶ Execute ──▶ (Fails on ambiguity or SQL error)

QueryPilot (Production Engine):
User ──▶ Intent ──▶ Ambiguity Check ──▶ Clarify ──▶ Schema & Glossary Retrieval
      ──▶ SQL Gen ──▶ SQLGlot AST Validation ──▶ Safe Execution ──▶ Self-Repair Loop
      ──▶ Result Sanity Check ──▶ Natural Explanation ──▶ Transparent SQL & Telemetry
```
