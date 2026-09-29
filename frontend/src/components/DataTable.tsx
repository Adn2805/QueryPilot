import { useState } from 'react';
import { Search, Download, X } from 'lucide-react';

interface Props {
  columns: string[];
  rows: Record<string, any>[];
  currencySymbol?: string;
  dimensionColumn?: string | null;
  onDimensionClick?: (value: string) => void;
}

export const DataTable = ({ columns, rows, currencySymbol = '₹', dimensionColumn, onDimensionClick }: Props) => {
  const [searchTerm, setSearchTerm] = useState('');

  if (!rows || rows.length === 0) {
    return (
      <div className="text-slate-400 text-center py-10 text-xs font-mono bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
        No records returned from query.
      </div>
    );
  }

  const filteredRows = rows.filter(row =>
    columns.some(col =>
      String(row[col] ?? '')
        .toLowerCase()
        .includes(searchTerm.toLowerCase())
    )
  );

  const exportCSV = () => {
    if (!rows.length) return;
    const header = columns.join(',');
    const csvRows = rows.map(r =>
      columns.map(c => `"${String(r[c] ?? '').replace(/"/g, '""')}"`).join(',')
    );
    const blob = new Blob([[header, ...csvRows].join('\n')], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `querypilot_export_${Date.now()}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const isNumericCol = (colName: string) => {
    return rows.some(r => typeof r[colName] === 'number');
  };

  const isDimensionCol = (colName: string) => {
    if (!dimensionColumn || !onDimensionClick) return false;
    return colName.toLowerCase() === dimensionColumn.toLowerCase();
  };

  const formatCellValue = (colName: string, val: any) => {
    if (val === null || val === undefined) return <span className="text-slate-300 italic font-mono text-[11px]">null</span>;
    
    // Status Badge
    if (colName.toLowerCase() === 'status') {
      const s = String(val).toLowerCase();
      const color =
        s === 'completed' || s === 'delivered'
          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
          : s === 'pending'
          ? 'bg-amber-50 text-amber-700 border-amber-200'
          : 'bg-rose-50 text-rose-700 border-rose-200';
      return (
        <span className={`inline-block px-2 py-0.5 rounded-md text-[10px] font-semibold border ${color}`}>
          {String(val)}
        </span>
      );
    }

    if (typeof val === 'number') {
      const c = colName.toLowerCase();
      if (c.includes('inr') || c.includes('amount') || c.includes('revenue') || c.includes('price') || c.includes('spent') || c.includes('spending') || c.includes('aov')) {
        return (
          <span className="tabular-nums font-semibold text-slate-800">
            {currencySymbol}{val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        );
      }
      if (c.includes('percent') || c.includes('share') || c.includes('pct')) {
        return (
          <span className="tabular-nums font-semibold text-blue-700">
            {val.toFixed(2)}%
          </span>
        );
      }
      return <span className="tabular-nums">{val.toLocaleString()}</span>;
    }

    return String(val);
  };

  return (
    <div className="flex flex-col space-y-2.5">
      {/* Search & Actions Bar */}
      <div className="flex items-center justify-between gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search records..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="w-full text-xs font-mono bg-white border border-slate-200 rounded-lg pl-8 pr-7 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              <X size={12} />
            </button>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-[11px] font-mono text-slate-400">
            {filteredRows.length} of {rows.length} rows
          </span>
          <button
            onClick={exportCSV}
            className="flex items-center space-x-1 text-xs font-medium text-slate-600 hover:text-slate-900 bg-white border border-slate-200 hover:border-slate-300 px-2.5 py-1.5 rounded-lg shadow-2xs transition"
          >
            <Download size={12} />
            <span>CSV</span>
          </button>
        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto rounded-xl border border-slate-200/90 bg-white shadow-2xs max-h-84 overflow-y-auto">
        <table className="w-full text-left text-xs text-slate-700">
          <thead className="sticky top-0 z-10 bg-slate-50 text-[11px] font-semibold text-slate-600 border-b border-slate-200 font-mono uppercase tracking-wider">
            <tr>
              {columns.map(col => {
                const numeric = isNumericCol(col);
                return (
                  <th
                    key={col}
                    className={`px-3.5 py-2.5 whitespace-nowrap ${numeric ? 'text-right' : 'text-left'}`}
                  >
                    {col.replace(/_/g, ' ')}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-mono text-[12px]">
            {filteredRows.map((row, idx) => (
              <tr key={idx} className="hover:bg-slate-50/70 transition-colors">
                {columns.map(col => {
                  const numeric = isNumericCol(col);
                  const clickable = isDimensionCol(col);
                  return (
                    <td
                      key={col}
                      className={`px-3.5 py-2 whitespace-nowrap ${numeric ? 'text-right' : 'text-left'} ${
                        clickable ? 'cursor-pointer' : ''
                      }`}
                      onClick={clickable ? () => onDimensionClick?.(String(row[col])) : undefined}
                    >
                      {clickable ? (
                        <span className="text-blue-700 hover:text-blue-900 underline decoration-dotted underline-offset-2 font-semibold">
                          {formatCellValue(col, row[col])}
                        </span>
                      ) : (
                        formatCellValue(col, row[col])
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
