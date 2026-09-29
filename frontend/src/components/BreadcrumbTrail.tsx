import { ChevronRight, Home, X } from 'lucide-react';
import type { DrillDownHistoryEntry } from '../types';

interface Props {
  history: DrillDownHistoryEntry[];
  onNavigate: (index: number) => void;
  onReset: () => void;
}

export const BreadcrumbTrail = ({ history, onNavigate, onReset }: Props) => {
  if (history.length === 0) return null;

  return (
    <div className="flex items-center gap-1 px-1 py-1.5 overflow-x-auto scrollbar-none">
      <button
        onClick={onReset}
        className="flex items-center space-x-1 text-[11px] font-mono font-medium text-slate-500 hover:text-blue-700 bg-slate-100 hover:bg-blue-50 border border-slate-200 hover:border-blue-200 px-2 py-1 rounded-md transition shrink-0"
        title="Back to original query"
      >
        <Home size={11} />
        <span>Root</span>
      </button>

      {history.map((entry, idx) => {
        const isLast = idx === history.length - 1;
        return (
          <div key={idx} className="flex items-center gap-1 shrink-0">
            <ChevronRight size={12} className="text-slate-300 shrink-0" />
            {isLast ? (
              <span className="flex items-center space-x-1 text-[11px] font-mono font-semibold text-slate-900 bg-blue-50 border border-blue-200 px-2 py-1 rounded-md">
                <span className="truncate max-w-[140px]">{entry.label}</span>
              </span>
            ) : (
              <button
                onClick={() => onNavigate(idx)}
                className="flex items-center space-x-1 text-[11px] font-mono font-medium text-slate-600 hover:text-blue-700 bg-white hover:bg-blue-50 border border-slate-200 hover:border-blue-200 px-2 py-1 rounded-md transition"
              >
                <span className="truncate max-w-[140px]">{entry.label}</span>
              </button>
            )}
          </div>
        );
      })}

      {history.length > 0 && (
        <button
          onClick={onReset}
          className="ml-1 text-slate-400 hover:text-rose-500 p-0.5 rounded-md hover:bg-rose-50 transition shrink-0"
          title="Clear drill-down trail"
        >
          <X size={12} />
        </button>
      )}
    </div>
  );
};
