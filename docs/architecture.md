# QueryPilot Architecture Reference

## 1. System Architecture Overview

QueryPilot is an enterprise-grade Conversational Text-to-SQL & Clarification Engine designed to eliminate the ambiguity and safety hazards of naive Text-to-SQL systems.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Frontend Layer (React + Vite + TypeScript)              │
│                                                                             │
│   ┌──────────────┐  ┌──────────────────┐  ┌────────────────┐  ┌──────────┐  │
│   │  Dashboard   │  │ Query Workspace  │  │ Schema Explorer│  │ Glossary │  │
│   │ (KPI & Feed) │  │ (Chat & Recharts)│  │ (Tables & FKs) │  │  (CRUD)  │  │
│   └──────────────┘  └──────────────────┘  └────────────────┘  └──────────┘  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP / JSON (Axios + TanStack Query)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FastAPI Backend & Orchestration                       │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      LangGraph State Machine Pipeline               │   │
│   │                                                                     │   │
│   │   User Query ──▶ Intent Analysis ──▶ Ambiguity Detection ────┐      │   │
│   │                                                              │      │   │
│   │   ┌──────────────────────────────────────────────────────────┘      │   │
│   │   ├──▶ Ambiguous? ──▶ Clarification Engine ──▶ User Selects Option  │   │
│   │   │                                                │                │   │
│   │   └──▶ Clear? ──▶ Schema & Glossary Retrieval ◀────┘                │   │
│   │                           │                                         │   │
│   │                           ▼                                         │   │
│   │                     SQL Generation                                  │   │
│   │                           │                                         │   │
│   │                           ▼                                         │   │
│   │               SQLGlot AST Security Validator                        │   │
│   │                           │                                         │   │
│   │              ┌────────────┴───────────┐                             │   │
│   │              ▼                        ▼                             │   │
│   │          [BLOCKED]                [VALID]                           │   │
│   │              │                        │                             │   │
│   │              │                        ▼                             │   │
│   │              │             Safe Read-Only DB Execution              │   │
│   │              │                        │                             │   │
│   │              │         ┌──────────────┴──────────────┐              │   │
│   │              │         ▼                             ▼              │   │
│   │              │     [FAILURE]                     [SUCCESS]          │   │
│   │              │         │                             │              │   │
│   │              │         ▼                             ▼              │   │
│   │              │    SQL Self-Repair            Result Validation      │   │
│   │              │   (Feedback Loop ≤ 3)                 │              │   │
│   │              │         │                             ▼              │   │
│   │              │         └──────────────┐     Natural Explanation     │   │
│   │              ▼                        │              │              │   │
│   │       Security Response               ▼              ▼              │   │
│   │              └─────────────────▶ Structured Final Response ◀────────┘   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────┬───────────────────┘
                       │                                  │
                       ▼                                  ▼
┌──────────────────────────────────────┐  ┌───────────────────────────────────┐
│     PostgreSQL Application DB        │  │   PostgreSQL Analytics DB (Demo)  │
│         (querypilot_app)             │  │       (querypilot_analytics)      │
│                                      │  │                                   │
│  • users (JWT Auth & RBAC)           │  │  • customers                      │
│  • conversations (Multi-turn state)  │  │  • orders                         │
│  • query_records (Audit & telemetry) │  │  • order_items                    │
│  • glossary_terms (Metrics & logic)  │  │  • products                       │
│  • evaluation_runs & results         │  │  • categories                     │
│  • pgvector embedding store          │  │  • payments, regions, employees   │
│  (Read/Write Connection)             │  │  (Dedicated READ-ONLY Role)       │
└──────────────────────────────────────┘  └───────────────────────────────────┘
```

---

## 2. Core Architectural Principles

### 1. "Don't let the AI guess what the user means"
Standard Text-to-SQL interfaces assume the user's intent is unambiguous and immediately guess column filters. QueryPilot uses a discrete **Ambiguity Detection Node** that identifies vague metrics ("best", "recent", "top", "active") and halts execution to present actionable multiple-choice options.

### 2. Multi-Turn Context Grounding
Conversations maintain multi-turn history. Follow-up refinements ("Only for 2025", "Sort descending by total spending") are merged into self-contained analytical queries before schema retrieval.

### 3. Focused Schema & Glossary Retrieval
Instead of dumping hundreds of database schema tokens into the LLM prompt for every turn, the system retrieves only the relevant tables, columns, foreign keys, and matching business definitions from the business glossary.

### 4. Defense in Depth
Security is enforced at two distinct layers:
1. **Application AST Validator (SQLGlot)**: Inspects the query AST to reject DDL/DML, enforce table allowlists, and inject safe row LIMIT clauses.
2. **Database Permissions**: Queries execute over a connection dedicated to `querypilot_readonly`, a PostgreSQL user with strict `SELECT` grants only.

### 5. Automated Self-Repair Loop
When database execution encounters a runtime error (e.g. column not found, grouping error, syntax issue), the error message and schema context are fed into the self-repair node to regenerate and re-validate corrected SQL up to 3 times before reporting an error.
