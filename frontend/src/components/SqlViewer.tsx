import { useState } from 'react';
import { Check, Copy, Terminal, Database } from 'lucide-react';

interface Props {
  sql: string;
}

export const SqlViewer = ({ sql }: Props) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lines = sql.trim().split('\n');

  return (
    <div className="relative rounded-xl overflow-hidden border border-slate-800 bg-[#0b0f17] shadow-lg">
      {/* Code Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#080b10] border-b border-slate-800/80 text-xs">
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500/80" />
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
          </div>
          <span className="text-slate-600">|</span>
          <div className="flex items-center space-x-1.5 text-slate-300 font-mono text-[11px]">
            <Terminal size={13} className="text-blue-400" />
            <span>query.sql</span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="flex items-center space-x-1 text-[10px] font-mono text-emerald-400/90 bg-emerald-950/40 border border-emerald-800/40 px-2 py-0.5 rounded-md">
            <Database size={10} />
            <span>PostgreSQL 16</span>
          </span>

          <button
            onClick={handleCopy}
            className="flex items-center space-x-1 text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 px-2.5 py-1 rounded-md text-[11px] font-mono transition"
          >
            {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      </div>

      {/* Code Body with Gutter */}
      <div className="p-4 overflow-x-auto flex text-xs font-mono leading-relaxed">
        {/* Line numbers gutter */}
        <div className="select-none text-slate-600 pr-4 text-right border-r border-slate-800/60 font-mono">
          {lines.map((_, i) => (
            <div key={i}>{i + 1}</div>
          ))}
        </div>

        {/* Code Content */}
        <pre className="pl-4 text-slate-100 font-mono whitespace-pre flex-1">
          {lines.map((line, idx) => (
            <div key={idx} className="hover:bg-slate-800/30 px-1 rounded-xs">
              <span className="text-blue-300 font-medium">{line}</span>
            </div>
          ))}
        </pre>
      </div>
    </div>
  );
};
