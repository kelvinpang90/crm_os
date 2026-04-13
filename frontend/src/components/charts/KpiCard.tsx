interface Props {
  title: string;
  value: number | string;
  prefix?: string;
  suffix?: string;
  change?: number | null;
}

export default function KpiCard({ title, value, prefix, suffix, change }: Props) {
  const formatted = typeof value === 'number'
    ? value >= 10000
      ? `${(value / 10000).toFixed(1)}万`
      : value.toLocaleString()
    : value;

  return (
    <div className="bg-dark-card border border-dark-border rounded-xl p-4">
      <p className="text-sm text-text-muted mb-1">{title}</p>
      <p className="text-2xl font-bold text-text-primary">
        {prefix}{formatted}{suffix}
      </p>
      {change != null && change !== 0 && (
        <p className={`text-xs mt-1 ${change > 0 ? 'text-green-400' : 'text-red-400'}`}>
          {change > 0 ? '↑' : '↓'} {Math.abs(change)}%
        </p>
      )}
    </div>
  );
}
