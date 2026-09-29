import { TrendingUp, ShoppingBag, IndianRupee, Users, Award, Hash, ArrowUpRight, Search as SearchIcon } from 'lucide-react';
import type { KPIMetric, DrillDownOption } from '../types';

interface Props {
  metrics: KPIMetric[];
  drilldownOptions?: DrillDownOption[];
  onExplore?: (option: DrillDownOption) => void;
}

export const SummaryCards = ({ metrics, drilldownOptions, onExplore }: Props) => {
  if (!metrics || metrics.length === 0) return null;

  const getMetricIcon = (label: string) => {
    const l = label.toLowerCase();
    if (l.includes('revenue') || l.includes('amount') || l.includes('spending') || l.includes('price')) {
      return <IndianRupee className="text-blue-600" size={18} />;
    }
    if (l.includes('order') || l.includes('sale')) {
      return <ShoppingBag className="text-emerald-600" size={18} />;
    }
    if (l.includes('customer') || l.includes('user')) {
      return <Users className="text-indigo-600" size={18} />;
    }
    if (l.includes('average') || l.includes('aov') || l.includes('trend')) {
      return <TrendingUp className="text-amber-600" size={18} />;
    }
    if (l.includes('top') || l.includes('best') || l.includes('rank')) {
      return <Award className="text-violet-600" size={18} />;
    }
    return <Hash className="text-slate-600" size={18} />;
  };

  const hasExplore = drilldownOptions && drilldownOptions.length > 0 && onExplore;

  return (
    <div className="space-y-3">
      <div
        className={`grid gap-3.5 ${
          metrics.length === 1
            ? 'grid-cols-1'
            : metrics.length === 2
            ? 'grid-cols-2'
            : 'grid-cols-1 md:grid-cols-3'
        }`}
      >
        {metrics.map((m, idx) => (
          <div
            key={idx}
            className="group relative bg-white rounded-xl border border-slate-200/90 p-4.5 shadow-2xs hover:border-slate-300 hover:shadow-xs transition-all duration-200"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 font-mono">
                {m.label}
              </span>
              <div className="w-8 h-8 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-center shrink-0 text-slate-700 group-hover:bg-slate-100/80 transition-colors">
                {getMetricIcon(m.label)}
              </div>
            </div>

            <div className="flex items-baseline justify-between">
              <div className="text-2xl font-bold tracking-tight text-slate-900 font-mono tabular-nums">
                {m.formatted}
              </div>
              {m.unit && (
                <span className="inline-flex items-center space-x-0.5 text-[10px] font-semibold text-slate-500 bg-slate-100/90 px-2 py-0.5 rounded-md border border-slate-200/60 uppercase tracking-wider">
                  <span>{m.unit}</span>
                  <ArrowUpRight size={10} className="text-slate-400" />
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Explore / drill-down quick actions for KPI results */}
      {hasExplore && (
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider mr-0.5">
            Explore:
          </span>
          {drilldownOptions!.slice(0, 4).map(opt => (
            <button
              key={opt.action_id}
              onClick={() => onExplore!(opt)}
              className="flex items-center space-x-1 text-[11px] font-mono font-medium text-slate-600 hover:text-blue-700 bg-white hover:bg-blue-50 border border-slate-200 hover:border-blue-200 px-2 py-1 rounded-md transition shadow-3xs"
            >
              <SearchIcon size={10} className="text-slate-400" />
              <span>{opt.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
