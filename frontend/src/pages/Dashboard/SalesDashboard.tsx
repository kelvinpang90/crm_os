import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { formatMYR } from '@/utils/currency';
import { dashboardApi } from '@/services/dashboard';
import type { KpiItem, PipelineStage } from '@/services/dashboard';
import KpiCard from '@/components/charts/KpiCard';
import Skeleton from '@/components/common/Skeleton';
import dayjs from 'dayjs';

const KPI_LABELS: Record<string, string> = {
  new_contacts_today: 'myNewContacts',
  follow_up_today: 'followUpToday',
  monthly_gmv: 'myMonthlyGmv',
  monthly_won_count: 'myWonCount',
  target_completion_rate: 'targetCompletion',
};

const KPI_CONFIG: Record<string, { prefix?: string; suffix?: string }> = {
  new_contacts_today: {},
  follow_up_today: {},
  monthly_gmv: { prefix: 'RM ' },
  monthly_won_count: {},
  target_completion_rate: { suffix: '%' },
};

const STAGE_LABELS: Record<string, string> = {
  newLead: 'funnelStages.newLead',
  contacted: 'funnelStages.contacted',
  quoting: 'funnelStages.quoting',
  won: 'funnelStages.won',
  lost: '已流失',
};

const STAGE_COLORS: Record<string, string> = {
  newLead: 'border-blue-500/50 from-blue-500/10',
  contacted: 'border-cyan-500/50 from-cyan-500/10',
  quoting: 'border-orange-500/50 from-orange-500/10',
  won: 'border-green-500/50 from-green-500/10',
  lost: 'border-red-500/50 from-red-500/10',
};

export default function SalesDashboard() {
  const { t } = useTranslation('dashboard');
  const [loading, setLoading] = useState(true);
  const [kpis, setKpis] = useState<KpiItem[]>([]);
  const [pipeline, setPipeline] = useState<PipelineStage[]>([]);

  useEffect(() => {
    (async () => {
      try {
        const res = await dashboardApi.getSales();
        setKpis(res.data.data.kpis);
        setPipeline(res.data.data.pipeline);
      } catch { /* ignore */ }
      setLoading(false);
    })();
  }, []);

  if (loading) return <Skeleton rows={8} />;

  return (
    <div className="space-y-4">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
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

      {/* Pipeline */}
      <div>
        <h3 className="text-sm font-semibold text-text-primary mb-3">{t('myPipeline')}</h3>
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
          {pipeline.map((stage) => {
            const colors = STAGE_COLORS[stage.stage] || 'border-dark-border from-dark-hover';
            return (
              <div
                key={stage.stage}
                className={`bg-gradient-to-b to-transparent border rounded-xl p-4 ${colors}`}
              >
                <p className="text-xs text-text-muted mb-2">
                  {t(STAGE_LABELS[stage.stage] || stage.stage, stage.stage)}
                </p>
                <p className="text-xl font-bold text-text-primary">{stage.count}</p>
                <p className="text-sm text-text-secondary mt-1">
                  {formatMYR(stage.amount)}
                </p>
                {stage.last_updated && (
                  <p className="text-xs text-text-muted mt-2">
                    {dayjs(stage.last_updated).format('MM-DD HH:mm')}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
