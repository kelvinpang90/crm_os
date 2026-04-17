import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { analyticsApi, type AnalyticsDashboard } from '@/services/analytics';
import { formatMYR } from '@/utils/currency';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, PieChart, Pie,
} from 'recharts';

const COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444'];

export default function AnalyticsPage() {
  const { t } = useTranslation('dashboard');
  const [data, setData] = useState<AnalyticsDashboard | null>(null);
  const [days, setDays] = useState(90);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    analyticsApi.getAnalytics(days)
      .then((res) => setData(res.data.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [days]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!data) return <p className="text-text-muted">{t('common:noData')}</p>;

  const { overview, conversion_trend, channel_distribution, sales_ranking } = data;

  const kpis = [
    { label: t('analytics.totalContacts'), value: overview.total_contacts },
    { label: t('analytics.totalWon'), value: overview.total_won },
    { label: t('analytics.totalLost'), value: overview.total_lost },
    { label: t('analytics.conversionRate'), value: `${overview.overall_conversion_rate}%` },
    { label: t('analytics.totalDealAmount'), value: formatMYR(overview.total_deal_amount) },
    { label: t('analytics.avgDealValue'), value: formatMYR(overview.avg_deal_value) },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-text-primary">{t('common:nav.analytics')}</h1>
        <div className="flex gap-2">
          {[30, 90, 180, 365].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1 text-sm rounded-lg border transition-colors ${
                days === d
                  ? 'border-primary bg-primary/10 text-primary'
                  : 'border-dark-border text-text-secondary hover:bg-dark-hover'
              }`}
            >
              {d}{t('days')}
            </button>
          ))}
        </div>
      </div>

      {/* Overview KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {kpis.map((kpi) => (
          <div key={kpi.label} className="bg-dark-card border border-dark-border rounded-xl p-4">
            <p className="text-xs text-text-muted mb-1">{kpi.label}</p>
            <p className="text-lg font-bold text-text-primary">{kpi.value}</p>
          </div>
        ))}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Conversion Trend */}
        <div className="bg-dark-card border border-dark-border rounded-xl p-4">
          <h3 className="text-sm font-semibold text-text-primary mb-4">{t('analytics.conversionTrend')}</h3>
          {conversion_trend.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={conversion_trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e2d4a" />
                <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0d1526', border: '1px solid #1e2d4a', borderRadius: 8 }}
                  labelStyle={{ color: '#e2e8f0' }}
                />
                <Line type="monotone" dataKey="new_contacts" stroke="#8b5cf6" strokeWidth={2} dot={false} name={t('analytics.newContacts')} />
                <Line type="monotone" dataKey="won" stroke="#10b981" strokeWidth={2} dot={false} name={t('analytics.wonContacts')} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-text-muted text-sm text-center py-8">{t('common:noData')}</p>
          )}
        </div>

        {/* Channel Distribution */}
        <div className="bg-dark-card border border-dark-border rounded-xl p-4">
          <h3 className="text-sm font-semibold text-text-primary mb-4">{t('analytics.channelDistribution')}</h3>
          {channel_distribution.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={channel_distribution}
                  dataKey="count"
                  nameKey="channel"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={({ channel, percentage }) => `${channel} ${percentage}%`}
                >
                  {channel_distribution.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0d1526', border: '1px solid #1e2d4a', borderRadius: 8 }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-text-muted text-sm text-center py-8">{t('common:noData')}</p>
          )}
        </div>
      </div>

      {/* Sales Ranking */}
      <div className="bg-dark-card border border-dark-border rounded-xl p-4">
        <h3 className="text-sm font-semibold text-text-primary mb-4">{t('analytics.salesRanking')}</h3>
        {sales_ranking.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-text-muted border-b border-dark-border">
                  <th className="text-left py-2 px-3">#</th>
                  <th className="text-left py-2 px-3">{t('analytics.salesperson')}</th>
                  <th className="text-right py-2 px-3">{t('analytics.dealCount')}</th>
                  <th className="text-right py-2 px-3">{t('analytics.dealAmount')}</th>
                  <th className="text-right py-2 px-3">{t('analytics.conversionRate')}</th>
                </tr>
              </thead>
              <tbody>
                {sales_ranking.map((s, i) => (
                  <tr key={s.user_id} className="border-b border-dark-border/50 hover:bg-dark-hover">
                    <td className="py-2 px-3 text-text-secondary">
                      {i < 3 ? ['🥇', '🥈', '🥉'][i] : i + 1}
                    </td>
                    <td className="py-2 px-3 text-text-primary font-medium">{s.user_name}</td>
                    <td className="py-2 px-3 text-right text-text-secondary">{s.deal_count}</td>
                    <td className="py-2 px-3 text-right text-text-secondary">
                      {formatMYR(s.deal_amount)}
                    </td>
                    <td className="py-2 px-3 text-right text-primary font-medium">{s.conversion_rate}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-text-muted text-sm text-center py-8">{t('common:noData')}</p>
        )}
      </div>
    </div>
  );
}
