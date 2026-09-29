import { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import {
  Sparkles,
  Send,
  Database,
  ShieldCheck,
  BarChart3,
  Table2,
  Code2,
  AlertCircle,
  HelpCircle,
  Clock,
  RefreshCw,
  Layers,
  ArrowRight,
  Trash2,
  TrendingUp,
  PieChart as PieIcon,
  Ban,
  Terminal,
  Cpu
} from 'lucide-react';
import type {
  ChatMessage, QueryResponse, HealthStatus, SampleQuery,
  DrillDownOption, FilterCondition, DrillDownRequest, DrillDownHistoryEntry
} from './types';
import { SummaryCards } from './components/SummaryCards';
import { DataVisualization } from './components/DataVisualization';
import { DataTable } from './components/DataTable';
import { SqlViewer } from './components/SqlViewer';
import { SchemaModal } from './components/SchemaModal';
import { BreadcrumbTrail } from './components/BreadcrumbTrail';
import { DrillDownMenu } from './components/DrillDownMenu';

const API_BASE = 'http://localhost:8000/api';

export function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [latestResponse, setLatestResponse] = useState<QueryResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'visual' | 'table' | 'sql'>('visual');
  
  // Modals & Metadata
  const [isSchemaOpen, setIsSchemaOpen] = useState(false);
  const [schemaMarkdown, setSchemaMarkdown] = useState('');
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [sampleQueries, setSampleQueries] = useState<SampleQuery[]>([]);

  // Drill-down state
  const [drilldownHistory, setDrilldownHistory] = useState<DrillDownHistoryEntry[]>([]);
  const [rootResponse, setRootResponse] = useState<QueryResponse | null>(null);
  const [originalQuery, setOriginalQuery] = useState<string | null>(null);
  const [selectedDrillValue, setSelectedDrillValue] = useState<string | null>(null);

  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Initial fetch
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [healthRes, schemaRes, sampleRes] = await Promise.all([
          axios.get(`${API_BASE}/health`),
          axios.get(`${API_BASE}/schema`),
          axios.get(`${API_BASE}/sample-queries`)
        ]);
        setHealth(healthRes.data);
        setSchemaMarkdown(schemaRes.data.schema_markdown);
        setSampleQueries(sampleRes.data);
      } catch (err) {
        console.error('Failed to initialize connection to backend:', err);
      }
    };
    fetchData();
  }, []);

  const handleClearChat = () => {
    setMessages([]);
    setLatestResponse(null);
    setDrilldownHistory([]);
    setRootResponse(null);
    setOriginalQuery(null);
    setSelectedDrillValue(null);
  };

  const handleSendQuery = async (queryText: string) => {
    const trimmed = queryText.trim();
    if (!trimmed || isLoading) return;

    const userMessage: ChatMessage = { role: 'user', content: trimmed };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInputQuery('');
    setIsLoading(true);

    // Reset drill-down state on new query
    setDrilldownHistory([]);
    setRootResponse(null);
    setSelectedDrillValue(null);

    try {
      const res = await axios.post<QueryResponse>(`${API_BASE}/query`, {
        message: trimmed,
        history: messages
      });

      const responseData = res.data;
      setLatestResponse(responseData);
      setOriginalQuery(trimmed);

      // Store root response for drill-down reset
      if (responseData.type === 'sql_result') {
        setRootResponse(responseData);
      }

      let assistantText = responseData.explanation || '';
      if (responseData.is_ambiguous && responseData.clarification_question) {
        assistantText = responseData.clarification_question;
      } else if (!responseData.is_supported && responseData.unsupported_reason) {
        assistantText = responseData.unsupported_reason;
      } else if (responseData.type === 'error' && responseData.error) {
        assistantText = responseData.error;
      }

      setMessages([
        ...newMessages,
        { role: 'assistant', content: assistantText }
      ]);

      // Auto set tab based on response structure
      if (responseData.type === 'sql_result') {
        if (responseData.is_kpi || (responseData.chart_type && responseData.chart_type !== 'table')) {
          setActiveTab('visual');
        } else {
          setActiveTab('table');
        }
      }
    } catch (err: any) {
      console.error('Query execution error:', err);
      const errMsg = err.response?.data?.detail || 'Failed to communicate with QueryPilot backend.';
      setMessages([
        ...newMessages,
        { role: 'assistant', content: `Execution Error: ${errMsg}` }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClarificationSelect = (option: string) => {
    handleSendQuery(option);
  };

  // --- Drill-Down Logic ---

  const getCurrentFilters = useCallback((): FilterCondition[] => {
    if (drilldownHistory.length > 0) {
      return drilldownHistory[drilldownHistory.length - 1].filters;
    }
    return latestResponse?.active_filters || [];
  }, [drilldownHistory, latestResponse]);

  const getCurrentMetric = useCallback((): string | null => {
    if (drilldownHistory.length > 0) {
      return drilldownHistory[drilldownHistory.length - 1].metric;
    }
    return latestResponse?.metric_name || null;
  }, [drilldownHistory, latestResponse]);

  const handleDrillDown = useCallback(async (
    option: DrillDownOption,
    clickedValue: string
  ) => {
    if (isLoading) return;
    setIsLoading(true);
    setSelectedDrillValue(null);

    const currentFilters = getCurrentFilters();
    const currentMetric = getCurrentMetric();
    const currentDimension = latestResponse?.dimension_name || latestResponse?.x_axis;

    // Build new filter from the clicked value
    const newFilter: FilterCondition = {
      dimension: currentDimension || 'unknown',
      value: clickedValue,
      display_label: `${(currentDimension || '').replace(/_/g, ' ')}: ${clickedValue}`
    };

    const updatedFilters = [...currentFilters, newFilter];
    const drillLabel = `${clickedValue} → ${option.label}`;

    const drillReq: DrillDownRequest = {
      target_action: option.action_id,
      target_dimension: option.target_dimension,
      current_metric: currentMetric,
      active_filters: updatedFilters,
      original_query: originalQuery,
      drilldown_label: drillLabel,
      history: messages
    };

    try {
      const res = await axios.post<QueryResponse>(`${API_BASE}/drill-down`, drillReq);
      const responseData = res.data;

      // Push current state to history before replacing
      const historyEntry: DrillDownHistoryEntry = {
        label: drillLabel,
        response: responseData,
        filters: updatedFilters,
        metric: currentMetric,
        originalQuery: originalQuery
      };

      setDrilldownHistory(prev => [...prev, historyEntry]);
      setLatestResponse(responseData);

      // Add drill-down context to chat
      setMessages(prev => [
        ...prev,
        { role: 'user', content: `📊 Drill-down: ${drillLabel}` },
        { role: 'assistant', content: responseData.explanation || `Showing ${option.label} for ${clickedValue}.` }
      ]);

      // Auto set tab
      if (responseData.type === 'sql_result') {
        if (responseData.is_kpi || (responseData.chart_type && responseData.chart_type !== 'table')) {
          setActiveTab('visual');
        } else {
          setActiveTab('table');
        }
      }
    } catch (err: any) {
      console.error('Drill-down error:', err);
      const errMsg = err.response?.data?.detail || 'Drill-down request failed.';
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: `Drill-down Error: ${errMsg}` }
      ]);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, getCurrentFilters, getCurrentMetric, latestResponse, originalQuery, messages]);

  const handleBreadcrumbNavigate = useCallback((index: number) => {
    if (index < 0 || index >= drilldownHistory.length) return;
    const entry = drilldownHistory[index];
    setLatestResponse(entry.response);
    setDrilldownHistory(prev => prev.slice(0, index + 1));
    setSelectedDrillValue(null);
  }, [drilldownHistory]);

  const handleBreadcrumbReset = useCallback(() => {
    if (rootResponse) {
      setLatestResponse(rootResponse);
    }
    setDrilldownHistory([]);
    setSelectedDrillValue(null);
  }, [rootResponse]);

  const handleChartElementClick = useCallback((dimensionValue: string) => {
    setSelectedDrillValue(dimensionValue);
  }, []);

  const handleDimensionCellClick = useCallback((dimensionValue: string) => {
    setSelectedDrillValue(dimensionValue);
  }, []);

  const handleDrillOptionSelect = useCallback((option: DrillDownOption) => {
    if (selectedDrillValue) {
      handleDrillDown(option, selectedDrillValue);
    }
  }, [selectedDrillValue, handleDrillDown]);

  const handleKpiExplore = useCallback((option: DrillDownOption) => {
    // For KPI cards, drill down with the metric label as context
    const kpiLabel = latestResponse?.kpi_metrics?.[0]?.label || 'Result';
    handleDrillDown(option, kpiLabel);
  }, [handleDrillDown, latestResponse]);

  // Get current drill-down options from response
  const drilldownOptions = latestResponse?.drilldown_options || [];
  const hasDrillDown = drilldownOptions.length > 0 && latestResponse?.type === 'sql_result';

  return (
    <div className="flex flex-col h-screen bg-[#f6f8fa] text-slate-900 antialiased font-sans selection:bg-blue-500 selection:text-white">
      {/* Top Pro Header Bar */}
      <header className="h-15 bg-white border-b border-slate-200/80 px-5 flex items-center justify-between shadow-2xs shrink-0 z-20">
        <div className="flex items-center space-x-3.5">
          <div className="w-8.5 h-8.5 rounded-lg bg-slate-900 flex items-center justify-center text-white shadow-xs border border-slate-800">
            <Terminal size={17} className="text-blue-400" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-slate-900 text-[15px] tracking-tight font-mono">
                QueryPilot
              </span>
              <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 border border-slate-200/80">
                v2.1 Pro
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2.5">
          {/* Status Chip */}
          <div className="hidden sm:flex items-center space-x-2 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 text-[11px] font-mono">
            <span
              className={`w-2 h-2 rounded-full ${
                health?.database_connected ? 'bg-emerald-500 ring-2 ring-emerald-500/20 animate-pulse' : 'bg-rose-500'
              }`}
            />
            <span className="text-slate-700 font-medium">PostgreSQL 16</span>
            <span className="text-slate-300">/</span>
            <span className="text-slate-500 capitalize flex items-center space-x-1">
              <Cpu size={11} className="text-slate-400" />
              <span>{health?.llm_provider || 'OpenAI'}</span>
            </span>
          </div>

          {/* Schema Inspector Button */}
          <button
            onClick={() => setIsSchemaOpen(true)}
            className="flex items-center space-x-1.5 bg-white hover:bg-slate-50 text-slate-700 hover:text-slate-900 border border-slate-200/90 text-xs font-medium px-3 py-1.5 rounded-lg shadow-2xs transition"
          >
            <Database size={13} className="text-slate-500" />
            <span>Schema</span>
            <kbd className="hidden md:inline-block text-[10px] font-mono bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded-sm ml-1 border border-slate-200">
              ⌥S
            </kbd>
          </button>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <main className="flex-1 flex overflow-hidden p-4 gap-4">
        {/* Left Pane: Conversational Query Studio */}
        <section className="w-1/2 flex flex-col bg-white rounded-2xl border border-slate-200/90 shadow-2xs overflow-hidden">
          {/* Sample Prompts Ribbon */}
          <div className="p-2.5 bg-slate-50/70 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center space-x-1.5 overflow-x-auto whitespace-nowrap scrollbar-none pb-0.5 pr-2">
              <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider pl-1 mr-1">
                Prompts:
              </span>
              {sampleQueries.map((s, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendQuery(s.query)}
                  className="text-[11px] font-mono bg-white hover:bg-slate-100 text-slate-700 border border-slate-200/90 hover:border-slate-300 px-2.5 py-1 rounded-md transition flex items-center space-x-1.5 shrink-0 shadow-3xs active:scale-98"
                >
                  {s.type === 'clarification' ? (
                    <HelpCircle size={11} className="text-amber-500 shrink-0" />
                  ) : s.type === 'security' ? (
                    <ShieldCheck size={11} className="text-rose-500 shrink-0" />
                  ) : s.type === 'unsupported' ? (
                    <Ban size={11} className="text-purple-500 shrink-0" />
                  ) : (
                    <BarChart3 size={11} className="text-blue-500 shrink-0" />
                  )}
                  <span>{s.query}</span>
                </button>
              ))}
            </div>

            {messages.length > 0 && (
              <button
                onClick={handleClearChat}
                title="Reset conversation"
                className="text-slate-400 hover:text-rose-600 p-1 rounded-md hover:bg-rose-50 transition shrink-0 ml-1"
              >
                <Trash2 size={14} />
              </button>
            )}
          </div>

          {/* Conversation Stream */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-400 space-y-3">
                <div className="w-12 h-12 rounded-xl bg-slate-100 text-slate-500 flex items-center justify-center border border-slate-200/60 shadow-2xs">
                  <Terminal size={22} className="text-slate-700" />
                </div>
                <div className="space-y-1 max-w-sm">
                  <h3 className="font-semibold text-slate-800 text-sm">Natural Language Data Query</h3>
                  <p className="text-xs text-slate-500 leading-relaxed">
                    Ask questions across sales, customers, products, and order timelines. The engine parses intent, resolves ambiguities, and runs validated PostgreSQL SELECT queries.
                  </p>
                </div>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex flex-col ${
                    msg.role === 'user' ? 'items-end' : 'items-start'
                  }`}
                >
                  <div
                    className={`max-w-[90%] rounded-xl px-4 py-2.5 text-xs leading-relaxed shadow-2xs ${
                      msg.role === 'user'
                        ? 'bg-slate-900 text-white font-medium rounded-br-none'
                        : 'bg-slate-100/90 text-slate-800 rounded-bl-none border border-slate-200/80 font-normal'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>

                    {/* Clarification Action Cards */}
                    {msg.role === 'assistant' &&
                      latestResponse?.is_ambiguous &&
                      idx === messages.length - 1 &&
                      latestResponse.clarification_options && (
                        <div className="mt-3 pt-2.5 border-t border-slate-200/90 space-y-1.5">
                          <p className="text-[11px] font-mono font-semibold text-slate-600 flex items-center space-x-1">
                            <HelpCircle size={12} className="text-amber-500" />
                            <span>Select target metric definition:</span>
                          </p>
                          <div className="grid grid-cols-1 gap-1.5 pt-0.5">
                            {latestResponse.clarification_options.map((opt, optIdx) => (
                              <button
                                key={optIdx}
                                onClick={() => handleClarificationSelect(opt)}
                                className="text-left text-xs bg-white hover:bg-blue-50 text-slate-800 hover:text-blue-700 border border-slate-200 hover:border-blue-300 px-3 py-2 rounded-lg font-medium transition flex items-center justify-between group shadow-3xs active:scale-99"
                              >
                                <span className="flex items-center space-x-2">
                                  <span className="w-4 h-4 rounded-full bg-slate-100 text-slate-500 group-hover:bg-blue-100 group-hover:text-blue-600 text-[10px] font-mono font-bold flex items-center justify-center shrink-0">
                                    {optIdx + 1}
                                  </span>
                                  <span>{opt}</span>
                                </span>
                                <ArrowRight size={12} className="text-slate-400 group-hover:text-blue-600 group-hover:translate-x-0.5 transition-all" />
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                  </div>
                </div>
              ))
            )}

            {isLoading && (
              <div className="flex items-center space-x-2 text-slate-500 text-xs py-1.5 bg-slate-50 px-3 rounded-lg w-fit border border-slate-200 font-mono">
                <RefreshCw size={12} className="animate-spin text-blue-600" />
                <span>{drilldownHistory.length > 0 ? 'Executing drill-down query...' : 'Evaluating intent & schema relationships...'}</span>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Pro Query Input Bar */}
          <div className="p-3 bg-white border-t border-slate-100">
            <form
              onSubmit={e => {
                e.preventDefault();
                handleSendQuery(inputQuery);
              }}
              className="flex items-center space-x-2 bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 focus-within:ring-2 focus-within:ring-slate-900/10 focus-within:border-slate-400 transition"
            >
              <input
                type="text"
                placeholder="Ask about revenue, orders, categories, customer spending..."
                value={inputQuery}
                onChange={e => setInputQuery(e.target.value)}
                disabled={isLoading}
                className="flex-1 bg-transparent text-xs text-slate-900 placeholder-slate-400 focus:outline-none py-1.5 font-normal"
              />
              <button
                type="submit"
                disabled={!inputQuery.trim() || isLoading}
                className="w-8 h-8 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-200 text-white rounded-lg flex items-center justify-center transition shadow-xs disabled:cursor-not-allowed shrink-0"
              >
                <Send size={13} />
              </button>
            </form>
          </div>
        </section>

        {/* Right Pane: Results & Analytical Studio */}
        <section className="w-1/2 flex flex-col bg-white rounded-2xl border border-slate-200/90 shadow-2xs overflow-hidden">
          {/* Segmented Control Header */}
          <div className="px-4 py-2.5 border-b border-slate-200 flex items-center justify-between bg-slate-50/80">
            <div className="flex items-center space-x-1 bg-slate-200/70 p-0.5 rounded-lg">
              <button
                onClick={() => setActiveTab('visual')}
                disabled={!latestResponse || latestResponse.type !== 'sql_result'}
                className={`flex items-center space-x-1.5 text-xs font-medium px-3 py-1.5 rounded-md transition ${
                  activeTab === 'visual'
                    ? 'bg-white text-slate-900 shadow-2xs'
                    : 'text-slate-600 hover:text-slate-900 disabled:opacity-40'
                }`}
              >
                {latestResponse?.is_kpi ? (
                  <TrendingUp size={13} />
                ) : latestResponse?.chart_type === 'pie' ? (
                  <PieIcon size={13} />
                ) : (
                  <BarChart3 size={13} />
                )}
                <span>{latestResponse?.is_kpi ? 'KPI Metrics' : 'Visual Studio'}</span>
              </button>
              <button
                onClick={() => setActiveTab('table')}
                disabled={!latestResponse || latestResponse.type !== 'sql_result'}
                className={`flex items-center space-x-1.5 text-xs font-medium px-3 py-1.5 rounded-md transition ${
                  activeTab === 'table'
                    ? 'bg-white text-slate-900 shadow-2xs'
                    : 'text-slate-600 hover:text-slate-900 disabled:opacity-40'
                }`}
              >
                <Table2 size={13} />
                <span>Table</span>
                {latestResponse?.row_count !== undefined && (
                  <span className="text-[10px] font-mono bg-slate-100 text-slate-600 px-1 rounded-sm ml-0.5">
                    {latestResponse.row_count}
                  </span>
                )}
              </button>
              <button
                onClick={() => setActiveTab('sql')}
                disabled={!latestResponse?.sql}
                className={`flex items-center space-x-1.5 text-xs font-medium px-3 py-1.5 rounded-md transition ${
                  activeTab === 'sql'
                    ? 'bg-white text-slate-900 shadow-2xs'
                    : 'text-slate-600 hover:text-slate-900 disabled:opacity-40'
                }`}
              >
                <Code2 size={13} />
                <span>SQL</span>
              </button>
            </div>

            {/* Performance Stats */}
            {latestResponse?.type === 'sql_result' && (
              <div className="flex items-center space-x-2 text-[11px] text-slate-500 font-mono">
                <span className="flex items-center space-x-1">
                  <Clock size={11} className="text-slate-400" />
                  <span>{latestResponse.execution_time_ms} ms</span>
                </span>
                <span className="text-slate-300">•</span>
                <span>{latestResponse.row_count} rows</span>
              </div>
            )}
          </div>

          {/* Breadcrumb Trail (if drilling down) */}
          {drilldownHistory.length > 0 && (
            <div className="px-4 py-1.5 bg-blue-50/50 border-b border-blue-100">
              <BreadcrumbTrail
                history={drilldownHistory}
                onNavigate={handleBreadcrumbNavigate}
                onReset={handleBreadcrumbReset}
              />
            </div>
          )}

          {/* Tab Content Canvas */}
          <div className="flex-1 overflow-y-auto p-4 flex flex-col justify-start space-y-3.5">
            {!latestResponse ? (
              <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 space-y-2">
                <Layers size={36} className="text-slate-300" />
                <p className="text-xs font-semibold text-slate-700">Analytical Canvas</p>
                <p className="text-[11px] text-slate-400 max-w-xs">
                  Run a query on the left to inspect generated SQL, charts, KPI aggregates, and raw record tables.
                </p>
              </div>
            ) : latestResponse.type === 'unsupported' ? (
              <div className="bg-purple-50/70 border border-purple-200/80 rounded-xl p-5 text-purple-900 space-y-2.5">
                <div className="flex items-center space-x-2 font-semibold text-xs text-purple-800">
                  <Ban size={15} className="text-purple-600" />
                  <span>Unsupported Domain / Entity</span>
                </div>
                <p className="text-xs leading-relaxed text-purple-800">{latestResponse.unsupported_reason}</p>
                <div className="p-3 bg-white/90 rounded-lg border border-purple-100 text-[11px] font-mono text-purple-700">
                  <span className="font-bold">Available Tables: </span>
                  <span>customers • products • orders • order_items</span>
                </div>
              </div>
            ) : latestResponse.type === 'error' ? (
              <div className="bg-rose-50/80 border border-rose-200 rounded-xl p-4.5 text-rose-900 space-y-2">
                <div className="flex items-center space-x-2 font-semibold text-xs text-rose-800">
                  <AlertCircle size={15} className="text-rose-600" />
                  <span>Execution & Security Check</span>
                </div>
                <p className="text-xs leading-relaxed font-mono text-rose-700">{latestResponse.error}</p>
                {latestResponse.sql && (
                  <div className="mt-2.5">
                    <SqlViewer sql={latestResponse.sql} />
                  </div>
                )}
              </div>
            ) : latestResponse.is_ambiguous ? (
              <div className="bg-amber-50/70 border border-amber-200 rounded-xl p-5 text-amber-900 space-y-2.5">
                <div className="flex items-center space-x-2 font-semibold text-xs text-amber-800">
                  <HelpCircle size={15} className="text-amber-600" />
                  <span>Ambiguity Clarification Required</span>
                </div>
                <p className="text-xs leading-relaxed text-amber-800">{latestResponse.explanation}</p>
                <p className="text-xs font-semibold text-amber-900">
                  Select one of the numbered definition cards on the left to execute the exact calculation.
                </p>
              </div>
            ) : (
              <div className="flex flex-col space-y-3.5">
                {/* Visual Tab */}
                {activeTab === 'visual' && (
                  <div className="space-y-3.5">
                    {/* Summary KPI Cards */}
                    {latestResponse.kpi_metrics && latestResponse.kpi_metrics.length > 0 && (
                      <SummaryCards
                        metrics={latestResponse.kpi_metrics}
                        drilldownOptions={drilldownOptions}
                        onExplore={hasDrillDown ? handleKpiExplore : undefined}
                      />
                    )}

                    {/* Chart Visualization */}
                    {latestResponse.chart_type &&
                      latestResponse.chart_type !== 'table' &&
                      latestResponse.chart_type !== 'kpi' &&
                      (latestResponse.rows?.length || 0) > 1 && (
                        <div className="bg-white p-3.5 rounded-xl border border-slate-200/90 shadow-2xs">
                          <div className="flex items-center justify-between mb-1 px-1">
                            <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-500">
                              {latestResponse.chart_type} Visualization
                            </span>
                            <div className="flex items-center space-x-2">
                              {hasDrillDown && (
                                <span className="text-[10px] font-mono text-blue-500">
                                  Click a bar/slice to explore
                                </span>
                              )}
                              <span className="text-[10px] font-mono text-slate-400">
                                Dim: {latestResponse.x_axis || 'Category'} | Metric: {latestResponse.y_axis || 'Value'}
                              </span>
                            </div>
                          </div>
                          <DataVisualization
                            data={latestResponse.rows || []}
                            chartType={latestResponse.chart_type}
                            xAxisKey={latestResponse.x_axis}
                            yAxisKey={latestResponse.y_axis}
                            currencySymbol={health?.currency_symbol || '₹'}
                            onElementClick={hasDrillDown ? handleChartElementClick : undefined}
                          />
                        </div>
                      )}

                    {/* Drill-Down Menu (appears when a value is selected) */}
                    {selectedDrillValue && hasDrillDown && (
                      <div className="flex items-center gap-2 px-1">
                        <DrillDownMenu
                          options={drilldownOptions}
                          selectedValue={selectedDrillValue}
                          onSelect={handleDrillOptionSelect}
                        />
                        <button
                          onClick={() => setSelectedDrillValue(null)}
                          className="text-[11px] font-mono text-slate-400 hover:text-slate-600 transition"
                        >
                          Dismiss
                        </button>
                      </div>
                    )}

                    {/* If single row, show small table preview beneath KPIs */}
                    {latestResponse.rows && latestResponse.rows.length === 1 && (
                      <div className="pt-1">
                        <DataTable
                          columns={latestResponse.columns || []}
                          rows={latestResponse.rows || []}
                          currencySymbol={health?.currency_symbol || '₹'}
                        />
                      </div>
                    )}
                  </div>
                )}

                {/* Table Tab */}
                {activeTab === 'table' && (
                  <div className="space-y-3">
                    <DataTable
                      columns={latestResponse.columns || []}
                      rows={latestResponse.rows || []}
                      currencySymbol={health?.currency_symbol || '₹'}
                      dimensionColumn={hasDrillDown ? (latestResponse.x_axis || latestResponse.dimension_name) : undefined}
                      onDimensionClick={hasDrillDown ? handleDimensionCellClick : undefined}
                    />
                    {/* Drill-Down Menu for table dimension clicks */}
                    {selectedDrillValue && hasDrillDown && (
                      <div className="flex items-center gap-2 px-1">
                        <DrillDownMenu
                          options={drilldownOptions}
                          selectedValue={selectedDrillValue}
                          onSelect={handleDrillOptionSelect}
                        />
                        <button
                          onClick={() => setSelectedDrillValue(null)}
                          className="text-[11px] font-mono text-slate-400 hover:text-slate-600 transition"
                        >
                          Dismiss
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* SQL Tab */}
                {activeTab === 'sql' && latestResponse.sql && (
                  <SqlViewer sql={latestResponse.sql} />
                )}

                {/* Explanatory summary & query metadata box */}
                {latestResponse.explanation && (
                  <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3 text-xs text-slate-600 flex items-start space-x-2">
                    <Sparkles size={14} className="text-blue-600 mt-0.5 shrink-0" />
                    <div className="space-y-0.5">
                      <span className="font-semibold text-slate-800 text-[11px] font-mono uppercase tracking-wider">
                        Calculation Notes:
                      </span>
                      <p className="leading-relaxed text-slate-600">{latestResponse.explanation}</p>
                    </div>
                  </div>
                )}

                {/* Active Filters Display */}
                {latestResponse.active_filters && latestResponse.active_filters.length > 0 && (
                  <div className="flex items-center gap-1.5 flex-wrap px-1">
                    <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                      Active Filters:
                    </span>
                    {latestResponse.active_filters.map((f, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] font-mono font-medium bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-md"
                      >
                        {f.display_label || `${f.dimension}: ${f.value}`}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </section>
      </main>

      {/* Schema Modal */}
      <SchemaModal
        isOpen={isSchemaOpen}
        onClose={() => setIsSchemaOpen(false)}
        schemaMarkdown={schemaMarkdown}
      />
    </div>
  );
}

export default App;
