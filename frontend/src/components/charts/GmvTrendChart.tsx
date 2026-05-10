import { useTranslation } from 'react-i18next';
import { formatMYR } from '@/utils/currency';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import type { GmvTrendPoint } from '@/services/dashboard';
import clsx from 'clsx';

interface Props {
  data: GmvTrendPoint[];
  period: 'month' | 'year';
  onPeriodChange: (period: 'month' | 'year') => void;
  title?: string;
}

export default function GmvTrendChart({ data, period, onPeriodChange, title }: Props) {
  const { t } = useTranslation('dashboard');

  return (
    <div className="bg-dark-card border border-dark-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        {title && <h3 className="text-sm font-semibold text-text-primary">{title}</h3>}
        <div className="flex gap-1">
          {(['month', 'year'] as const).map((p) => (
            <button
              key={p}
              onClick={() => onPeriodChange(p)}
              className={clsx(
                'px-3 py-1 text-xs rounded-md transition-colors',
                period === p
                  ? 'bg-primary text-white'
                  : 'bg-dark-hover text-text-muted hover:text-text-secondary'
              )}
            >
              {p === 'month' ? 'Month' : 'Year'}
            </button>
          ))}
        </div>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e2d4a" />
          <XAxis
            dataKey="label"
            stroke="#64748b"
            fontSize={11}
            tickLine={false}
          />
          <YAxis
            stroke="#64748b"
            fontSize={11}
            tickLine={false}
            tickFormatter={(v: number) =>
              v >= 1_000_000 ? `RM ${(v / 1_000_000).toFixed(1)}M` : v >= 1_000 ? `RM ${(v / 1_000).toFixed(0)}K` : `RM ${v}`
            }
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#0d1526',
              border: '1px solid #1e2d4a',
              borderRadius: '8px',
              color: '#f1f5f9',
              fontSize: '12px',
            }}
            formatter={(value: number) => [formatMYR(value), 'GMV']}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: '#3b82f6', r: 3 }}
            activeDot={{ r: 5, fill: '#8b5cf6' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
