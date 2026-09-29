-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'analyst' CHECK (role IN ('admin', 'analyst')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500),
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Query records table (comprehensive query history)
CREATE TABLE IF NOT EXISTS query_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    natural_query TEXT NOT NULL,
    resolved_intent TEXT,
    detected_ambiguity TEXT,
    clarification_steps JSONB DEFAULT '[]',
    retrieved_tables TEXT[] DEFAULT '{}',
    generated_sql TEXT,
    final_sql TEXT,
    validation_result JSONB,
    execution_status VARCHAR(50) DEFAULT 'pending' CHECK (execution_status IN ('pending', 'success', 'error', 'timeout', 'blocked', 'clarification_needed', 'unsupported', 'greeting', 'validation_failed', 'execution_failed', 'repair_failed', 'system_error')),
    query_result JSONB,
    natural_explanation TEXT,
    visualization_type VARCHAR(20),
    row_count INTEGER,
    retry_count INTEGER DEFAULT 0,
    llm_latency_ms FLOAT,
    retrieval_latency_ms FLOAT,
    validation_latency_ms FLOAT,
    execution_latency_ms FLOAT,
    total_latency_ms FLOAT,
    error_message TEXT,
    error_category VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Business glossary terms
CREATE TABLE IF NOT EXISTS glossary_terms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    term VARCHAR(255) UNIQUE NOT NULL,
    definition TEXT NOT NULL,
    sql_expression TEXT,
    related_tables TEXT[] DEFAULT '{}',
    related_columns TEXT[] DEFAULT '{}',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Schema metadata with embeddings
CREATE TABLE IF NOT EXISTS schema_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(255) NOT NULL,
    column_name VARCHAR(255),
    data_type VARCHAR(100),
    description TEXT,
    sample_values TEXT[] DEFAULT '{}',
    is_primary_key BOOLEAN DEFAULT FALSE,
    foreign_key_ref VARCHAR(500),
    embedding vector(384),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(table_name, column_name)
);

-- Evaluation run records
CREATE TABLE IF NOT EXISTS evaluation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_name VARCHAR(255) NOT NULL,
    run_type VARCHAR(50) NOT NULL CHECK (run_type IN ('baseline', 'querypilot')),
    total_queries INTEGER DEFAULT 0,
    successful INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    metrics JSONB DEFAULT '{}',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Individual evaluation results
CREATE TABLE IF NOT EXISTS evaluation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES evaluation_runs(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL,
    natural_query TEXT NOT NULL,
    expected_sql TEXT,
    generated_sql TEXT,
    sql_correct BOOLEAN,
    execution_success BOOLEAN,
    clarification_triggered BOOLEAN DEFAULT FALSE,
    clarification_correct BOOLEAN,
    unsafe_blocked BOOLEAN DEFAULT FALSE,
    latency_ms FLOAT,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_query_records_conversation_id ON query_records(conversation_id);
CREATE INDEX IF NOT EXISTS idx_query_records_user_id ON query_records(user_id);
CREATE INDEX IF NOT EXISTS idx_query_records_created_at ON query_records(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_evaluation_results_run_id ON evaluation_results(run_id);
CREATE INDEX IF NOT EXISTS idx_schema_metadata_table ON schema_metadata(table_name);
