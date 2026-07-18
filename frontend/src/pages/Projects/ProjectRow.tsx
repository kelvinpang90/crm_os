import { useTranslation } from 'react-i18next';
import { stepName, getAlertLevel, getStaleDays, TOTAL_STEPS } from './steps';
import type { Project, ProjectAlertLevel } from '@/types';

// Static Tailwind classes per alert level (kept literal so JIT picks them up).
const ALERT: Record<ProjectAlertLevel, { border: string; dot: string; text: string; seg: string }> = {
  normal: { border: 'border-l-status-following', dot: 'bg-status-following', text: 'text-status-following', seg: 'bg-status-following' },
  watch: { border: 'border-l-status-negotiating', dot: 'bg-status-negotiating', text: 'text-status-negotiating', seg: 'bg-status-negotiating' },
  urgent: { border: 'border-l-status-lost', dot: 'bg-status-lost', text: 'text-status-lost', seg: 'bg-status-lost' },
  done: { border: 'border-l-dark-border', dot: 'bg-text-muted', text: 'text-text-muted', seg: 'bg-status-following' },
};

interface ProjectRowProps {
  project: Project;
  onClick?: (project: Project) => void;
}

export default function ProjectRow({ project, onClick }: ProjectRowProps) {
  const { t } = useTranslation('projects');
  const level = getAlertLevel(project);
  const days = getStaleDays(project.last_updated_at);
  const a = ALERT[level];
  const clickable = Boolean(onClick);

  const staleText = level === 'done' ? t('alert.done') : t('stale_days', { count: days });

  return (
    <div
      role={clickable ? 'button' : undefined}
      tabIndex={clickable ? 0 : undefined}
      onClick={onClick ? () => onClick(project) : undefined}
      onKeyDown={
        onClick
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onClick(project);
              }
            }
          : undefined
      }
      className={`grid grid-cols-1 sm:grid-cols-[minmax(0,170px)_minmax(0,1fr)_96px_64px] gap-x-3 gap-y-2 items-center px-4 py-3 border-b border-dark-border last:border-b-0 border-l-4 ${a.border} ${
        clickable ? 'cursor-pointer hover:bg-dark-hover transition-colors' : ''
      }`}
    >
      {/* Customer + address (+ stale on mobile) */}
      <div className="flex items-center gap-2 min-w-0">
        <span className={`w-2 h-2 rounded-full shrink-0 ${a.dot}`} />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-text-primary truncate">{project.customer_name}</p>
          <p className="text-xs text-text-muted truncate">{project.address}</p>
        </div>
        <span className={`sm:hidden text-xs font-medium shrink-0 ${a.text}`}>{staleText}</span>
      </div>

      {/* 12-step progress bar + step label */}
      <div className="min-w-0">
        <div className="flex gap-0.5">
          {Array.from({ length: TOTAL_STEPS }).map((_, idx) => {
            const step = idx + 1;
            const seg =
              step < project.current_step
                ? 'bg-status-following'
                : step === project.current_step
                ? a.seg
                : 'bg-dark-border opacity-60';
            return (
              <div
                key={step}
                title={stepName(step, t)}
                className={`h-2 flex-1 rounded-sm ${seg}`}
              />
            );
          })}
        </div>
        <p className="text-xs text-text-secondary mt-1 truncate">
          {t('step_label', { step: project.current_step, name: stepName(project.current_step, t) })}
        </p>
      </div>

      {/* Manager (desktop) */}
      <div className="hidden sm:block text-xs text-text-secondary truncate">{project.project_manager}</div>

      {/* Stale (desktop) */}
      <div className={`hidden sm:block text-right text-xs font-medium ${a.text}`}>{staleText}</div>
    </div>
  );
}
