import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { dashboardApi } from '@/services/dashboard';
import type { KpiItem, FunnelStage, LeaderboardEntry, GmvTrendPoint } from '@/services/dashboard';
import KpiCard from '@/components/charts/KpiCard';
import FunnelChart from '@/components/charts/FunnelChart';
import LeaderboardTable from '@/components/charts/LeaderboardTable';
import GmvTrendChart from '@/components/charts/GmvTrendChart';
import Skeleton from '@/components/common/Skeleton';

const KPI_CONFIG: Record<string, { prefix?: string; suffix?: string }> = {
  new_leads_today: {},
  follow_up_today: {},
  quoting_count: {},
  monthly_gmv: { prefix: '¥' },
  monthly_win_rate: { suffix: '%' },
  pipeline_value: { prefix: '¥' },
};

const KPI_LABELS: Record<string, string> = {
  new_leads_today: 'newLeadsToday',
  follow_up_today: 'followUpToday',
  quoting_count: 'quotingCount',
  monthly_gmv: 'monthlyGmv',
  monthly_win_rate: 'monthlyWinRate',
  pipeline_value: 'pipelineValue',
};

function currentMonth() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

export default function AdminDashboard() {
  const { t } = useTranslation('dashboard');
  const [loading, setLoading] = useState(true);
  const [kpis, setKpis] = useState<KpiItem[]>([]);
  const [funnel, setFunnel] = useState<FunnelStage[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [trendData, setTrendData] = useState<GmvTrendPoint[]>([]);
  const [trendPeriod, setTrendPeriod] = useState<'month' | 'year'>('month');
  const [lbMonth, setLbMonth] = useState(currentMonth());

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const [dashRes, lbRes, trendRes] = await Promise.all([
        dashboardApi.getAdmin(),
        dashboardApi.getLeaderboard(lbMonth),
        dashboardApi.getGmvTrend(trendPeriod),
      ]);
      setKpis(dashRes.data.data.kpis);
      setFunnel(dashRes.data.data.funnel);
      setLeaderboard(lbRes.data.data.entries);
      setTrendData(trendRes.data.data.data);
    } catch { /* ignore */ }
    setLoading(false);
  }, [lbMonth, trendPeriod]);

  useEffect(() => { loadDashboard(); }, [loadDashboard]);

  const handleLbMonthChange = (m: string) => setLbMonth(m);
  const handlePeriodChange = (p: 'month' | 'year') => setTrendPeriod(p);

  if (loading) return <Skeleton rows={8} />;

  return (
    <div className="space-y-4">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
        {kpis.map((kpi) => (
          <KpiCard
            key={kpi.key}
            title={t(KPI_LABELS[kpi.key] || kpi.key)}
            value={kpi.value}
            change={kpi.change}
            {...KPI_CONFIG[kpi.key]}
          />
        ))}
      </div>

      {/* Funnel + Leaderboard */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <FunnelChart stages={funnel} title={t('salesFunnel')} />
        <LeaderboardTable
          entries={leaderboard}
          title={t('leaderboard')}
          month={lbMonth}
          onMonthChange={handleLbMonthChange}
        />
      </div>

      {/* GMV Trend */}
      <GmvTrendChart
        data={trendData}
        period={trendPeriod}
        onPeriodChange={handlePeriodChange}
        title={t('gmvTrend')}
      />
    </div>
  );
}
