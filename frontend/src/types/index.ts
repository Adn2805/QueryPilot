export type MessageRole = 'user' | 'assistant';

export interface ChatMessage {
  role: MessageRole;
  content: string;
}

export type ChartType = 'table' | 'bar' | 'line' | 'pie' | 'donut' | 'kpi';

export interface KPIMetric {
  label: string;
  value: any;
  formatted: string;
  unit?: string | null;
}

export interface FilterCondition {
  dimension: string;
  value: string;
  display_label?: string | null;
}

export interface DrillDownOption {
  action_id: string;
  label: string;
  target_dimension: string;
  icon?: string | null;
  description?: string | null;
}

export interface DrillDownRequest {
  target_action: string;
  target_dimension?: string | null;
  current_metric?: string | null;
  active_filters: FilterCondition[];
  original_query?: string | null;
  drilldown_label?: string | null;
  history: ChatMessage[];
}

export interface QueryResponse {
  type: 'clarification' | 'sql_result' | 'unsupported' | 'error';
  question: string;
  is_supported: boolean;
  unsupported_reason?: string | null;
  is_ambiguous: boolean;
  clarification_question?: string | null;
  clarification_options?: string[];
  sql?: string | null;
  explanation?: string | null;
  columns?: string[];
  rows?: Record<string, any>[];
  row_count?: number;
  execution_time_ms?: number;
  is_kpi?: boolean;
  kpi_metrics?: KPIMetric[];
  chart_type?: ChartType;
  x_axis?: string | null;
  y_axis?: string | null;
  metric_name?: string | null;
  dimension_name?: string | null;
  drilldown_options?: DrillDownOption[];
  active_filters?: FilterCondition[];
  query_metadata?: Record<string, any>;
  error?: string | null;
}

export interface DrillDownHistoryEntry {
  label: string;
  response: QueryResponse;
  filters: FilterCondition[];
  metric: string | null;
  originalQuery: string | null;
}

export interface HealthStatus {
  status: string;
  database_connected: boolean;
  llm_provider: string;
  currency_symbol: string;
}

export interface SampleQuery {
  category: string;
  query: string;
  type: 'sql' | 'clarification' | 'security' | 'unsupported';
}
