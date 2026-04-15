import { useTranslation } from 'react-i18next';
import type { FunnelStage } from '@/services/dashboard';
import { formatMYR } from '@/utils/currency';

interface Props {
  stages: FunnelStage[];
  title?: string;
}

const STAGE_COLORS: Record<string, string> = {
  newLead: 'bg-blue-500',
  contacted: 'bg-cyan-500',
  qualified: 'bg-yellow-500',
  quoting: 'bg-orange-500',
  negotiating: 'bg-purple-500',
  won: 'bg-green-500',
};

export default function FunnelChart({ stages, title }: Props) {
  const { t } = useTranslation('dashboard');
  const maxCount = Math.max(...stages.map((s) => s.count), 1);

  return (
    <div className="bg-dark-card border border-dark-border rounded-xl p-4">
      {title && <h3 className="text-sm font-semibold text-text-primary mb-3">{title}</h3>}
      <div className="space-y-2">
        {stages.map((s) => {
          const pct = (s.count / maxCount) * 100;
          const color = STAGE_COLORS[s.stage] || 'bg-blue-500';
          return (
            <div key={s.stage}>
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="text-text-secondary">{t(`funnelStages.${s.stage}`, s.stage)}</span>
                <span className="text-text-muted">
                  {s.count} · {formatMYR(s.amount)}
                </span>
              </div>
              <div className="h-5 bg-dark-hover rounded-full overflow-hidden">
                <div
                  className={`h-full ${color} rounded-full transition-all duration-500`}
                  style={{ width: `${Math.max(pct, 2)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
