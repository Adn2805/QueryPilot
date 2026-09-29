import { useState, useRef, useEffect } from 'react';
import {
  MapPin, Tag, Users, BarChart3, TrendingUp,
  FileText, Grid3X3, ChevronDown
} from 'lucide-react';
import type { DrillDownOption } from '../types';

interface Props {
  options: DrillDownOption[];
  selectedValue: string;
  onSelect: (option: DrillDownOption) => void;
}

const ICON_MAP: Record<string, React.ReactNode> = {
  map: <MapPin size={13} />,
  tag: <Tag size={13} />,
  users: <Users size={13} />,
  bar: <BarChart3 size={13} />,
  line: <TrendingUp size={13} />,
  pie: <Grid3X3 size={13} />,
  table: <FileText size={13} />,
};

export const DrillDownMenu = ({ options, selectedValue, onSelect }: Props) => {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (!options || options.length === 0) return null;

  return (
    <div ref={menuRef} className="relative inline-block">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-1.5 text-[11px] font-mono font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 hover:border-blue-300 px-2.5 py-1.5 rounded-lg transition shadow-2xs"
      >
        <span>Explore "{selectedValue}"</span>
        <ChevronDown size={12} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1.5 w-72 bg-white rounded-xl border border-slate-200 shadow-lg z-50 overflow-hidden">
          <div className="px-3 py-2 bg-slate-50 border-b border-slate-100">
            <p className="text-[10px] font-mono font-bold text-slate-500 uppercase tracking-wider">
              Follow the Number
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Drill into <span className="font-semibold text-slate-600">{selectedValue}</span>
            </p>
          </div>
          <div className="py-1 max-h-72 overflow-y-auto">
            {options.map((opt) => (
              <button
                key={opt.action_id}
                onClick={() => {
                  onSelect(opt);
                  setIsOpen(false);
                }}
                className="w-full text-left px-3 py-2.5 hover:bg-blue-50 transition group flex items-start space-x-2.5"
              >
                <div className="w-7 h-7 rounded-lg bg-slate-100 group-hover:bg-blue-100 border border-slate-200 group-hover:border-blue-200 flex items-center justify-center text-slate-500 group-hover:text-blue-600 shrink-0 mt-0.5 transition">
                  {ICON_MAP[opt.icon || 'bar'] || <BarChart3 size={13} />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-slate-800 group-hover:text-blue-700 transition">
                    {opt.label}
                  </p>
                  {opt.description && (
                    <p className="text-[10px] text-slate-400 mt-0.5 truncate">
                      {opt.description}
                    </p>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
