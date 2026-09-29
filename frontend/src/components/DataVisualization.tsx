import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend
} from 'recharts';
import type { ChartType } from '../types';

interface Props {
  data: Record<string, any>[];
  chartType: ChartType;
  xAxisKey?: string | null;
  yAxisKey?: string | null;
  currencySymbol?: string;
  onElementClick?: (dimensionValue: string) => void;
}

const PALETTE = [
  '#2563eb', // Indigo / Royal Blue
  '#0d9488', // Teal
  '#d97706', // Amber
  '#7c3aed', // Purple
  '#db2777', // Pink
  '#0284c7', // Sky Blue
  '#059669', // Emerald
  '#ea580c'  // Orange
];

export const DataVisualization = ({
  data,
  chartType,
  xAxisKey,
  yAxisKey,
  currencySymbol = '₹',
  onElementClick
}: Props) => {
  if (!data || data.length === 0) {
    return (
      <div className="text-slate-400 text-center py-12 text-xs font-mono bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
        No dataset rows available to plot.
      </div>
    );
  }

  // Detect keys if not provided
  const keys = Object.keys(data[0]);
  const xKey = xAxisKey && keys.includes(xAxisKey) ? xAxisKey : keys[0];
  const numKey = keys.find(k => typeof data[0][k] === 'number');
  const yKey = yAxisKey && keys.includes(yAxisKey) ? yAxisKey : (numKey || keys[1] || keys[0]);

  const isCurrency =
    yKey.toLowerCase().includes('inr') ||
    yKey.toLowerCase().includes('revenue') ||
    yKey.toLowerCase().includes('amount') ||
    yKey.toLowerCase().includes('spending') ||
    yKey.toLowerCase().includes('price') ||
    yKey.toLowerCase().includes('aov');

  const isPercentage = yKey.toLowerCase().includes('percent') || yKey.toLowerCase().includes('share');

  const isClickable = !!onElementClick;

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const p = payload[0];
      const val = p.value;
      const formattedVal =
        typeof val === 'number'
          ? isCurrency
            ? `${currencySymbol}${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
            : isPercentage
            ? `${val.toFixed(2)}%`
            : val.toLocaleString()
          : val;

      return (
        <div className="bg-slate-900/95 backdrop-blur-xs text-white px-3 py-2 rounded-lg border border-slate-800 shadow-xl text-xs space-y-1">
          <p className="text-[11px] font-medium text-slate-400 font-mono truncate max-w-[200px]">{label}</p>
          <div className="flex items-center space-x-2 font-mono">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: p.color || '#3b82f6' }} />
            <span className="font-semibold text-white tabular-nums">{formattedVal}</span>
          </div>
          {isClickable && (
            <p className="text-[10px] text-blue-300 mt-0.5 font-mono">Click to explore →</p>
          )}
        </div>
      );
    }
    return null;
  };

  const handleBarClick = (entry: any) => {
    if (onElementClick && entry?.activePayload?.[0]?.payload) {
      const val = entry.activePayload[0].payload[xKey];
      if (val !== undefined && val !== null) {
        onElementClick(String(val));
      }
    }
  };

  const handlePieClick = (_: any, index: number) => {
    if (onElementClick && data[index]) {
      const val = data[index][xKey];
      if (val !== undefined && val !== null) {
        onElementClick(String(val));
      }
    }
  };

  if (chartType === 'bar') {
    return (
      <div className={`w-full h-76 pt-1 ${isClickable ? 'cursor-pointer' : ''}`}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{ top: 10, right: 20, left: 10, bottom: 45 }}
            onClick={handleBarClick}
          >
            <CartesianGrid strokeDasharray="2 2" stroke="#f1f5f9" vertical={false} />
            <XAxis
              dataKey={xKey}
              stroke="#94a3b8"
              fontSize={11}
              fontFamily="monospace"
              tickLine={false}
              axisLine={{ stroke: '#e2e8f0' }}
              angle={-20}
              textAnchor="end"
              interval={0}
            />
            <YAxis
              stroke="#94a3b8"
              fontSize={11}
              fontFamily="monospace"
              tickLine={false}
              axisLine={false}
              tickFormatter={val =>
                typeof val === 'number' && val >= 1000 ? `${(val / 1000).toFixed(0)}k` : val
              }
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey={yKey} fill="#2563eb" radius={[4, 4, 0, 0]} maxBarSize={48}>
              {data.map((_, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={PALETTE[index % PALETTE.length]}
                  className={isClickable ? 'cursor-pointer hover:opacity-80 transition-opacity' : ''}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (chartType === 'line') {
    return (
      <div className="w-full h-76 pt-1">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 30 }}>
            <CartesianGrid strokeDasharray="2 2" stroke="#f1f5f9" vertical={false} />
            <XAxis
              dataKey={xKey}
              stroke="#94a3b8"
              fontSize={11}
              fontFamily="monospace"
              tickLine={false}
              axisLine={{ stroke: '#e2e8f0' }}
            />
            <YAxis
              stroke="#94a3b8"
              fontSize={11}
              fontFamily="monospace"
              tickLine={false}
              axisLine={false}
              tickFormatter={val =>
                typeof val === 'number' && val >= 1000 ? `${(val / 1000).toFixed(0)}k` : val
              }
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey={yKey}
              stroke="#2563eb"
              strokeWidth={2.5}
              dot={{ r: 3.5, fill: '#2563eb', strokeWidth: 2, stroke: '#ffffff' }}
              activeDot={{ r: 5.5, fill: '#1d4ed8' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (chartType === 'pie' || chartType === 'donut') {
    return (
      <div className={`w-full h-76 flex items-center justify-center pt-1 ${isClickable ? 'cursor-pointer' : ''}`}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="bottom"
              height={32}
              iconType="circle"
              iconSize={8}
              wrapperStyle={{ fontSize: '11px', fontFamily: 'monospace', color: '#64748b' }}
            />
            <Pie
              data={data}
              dataKey={yKey}
              nameKey={xKey}
              cx="50%"
              cy="48%"
              innerRadius={48}
              outerRadius={88}
              paddingAngle={2}
              label={({ percent }: { percent?: number }) =>
                percent && percent > 0.05 ? `${(percent * 100).toFixed(0)}%` : ''
              }
              labelLine={false}
              onClick={handlePieClick}
            >
              {data.map((_, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={PALETTE[index % PALETTE.length]}
                  className={isClickable ? 'cursor-pointer hover:opacity-80 transition-opacity' : ''}
                />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return null;
};
