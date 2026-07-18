import { useState, useEffect, useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { projectsApi } from '@/services/projects';
import { getAlertLevel, getStaleDays } from './steps';
import ProjectRow from './ProjectRow';
import ProjectDetail from './ProjectDetail';
import ProjectFormModal from './ProjectFormModal';
import type { Project, ProjectAlertLevel } from '@/types';
import Skeleton from '@/components/common/Skeleton';
import EmptyState from '@/components/common/EmptyState';

type AlertFilter = 'all' | 'urgent' | 'watch' | 'normal';

export default function ProjectsPage() {
  const { t } = useTranslation('projects');
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [pmFilter, setPmFilter] = useState<string>('all');
  const [alertFilter, setAlertFilter] = useState<AlertFilter>('all');

  // Modal state
  const [detail, setDetail] = useState<Project | null>(null);
  const [form, setForm] = useState<{ open: boolean; project: Project | null }>({ open: false, project: null });
  const [deleteTarget, setDeleteTarget] = useState<Project | null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    try {
      setProjects(await projectsApi.getProjects());
    } catch {
      /* ignore */
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Summary reflects the whole portfolio (unaffected by filters).
  const summary = useMemo(() => {
    let inProgress = 0;
    let urgent = 0;
    let watch = 0;
    let delivered = 0;
    for (const p of projects) {
      const level = getAlertLevel(p);
      if (level === 'done') delivered += 1;
      else inProgress += 1;
      if (level === 'urgent') urgent += 1;
      if (level === 'watch') watch += 1;
    }
    return { inProgress, urgent, watch, delivered };
  }, [projects]);

  const managers = useMemo(
    () => Array.from(new Set(projects.map((p) => p.project_manager))).sort(),
    [projects]
  );

  // Filter, then sort: most-overdue first, delivered projects sink to the bottom.
  const visible = useMemo(() => {
    const rank: Record<ProjectAlertLevel, number> = { urgent: 0, watch: 1, normal: 2, done: 3 };
    return projects
      .filter((p) => (pmFilter === 'all' ? true : p.project_manager === pmFilter))
      .filter((p) => (alertFilter === 'all' ? true : getAlertLevel(p) === alertFilter))
      .sort((a, b) => {
        const la = getAlertLevel(a);
        const lb = getAlertLevel(b);
        if (la !== lb) return rank[la] - rank[lb];
        return getStaleDays(b.last_updated_at) - getStaleDays(a.last_updated_at);
      });
  }, [projects, pmFilter, alertFilter]);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await projectsApi.deleteProject(deleteTarget.id);
      setDeleteTarget(null);
      await load();
    } catch {
      /* ignore */
    }
    setDeleting(false);
  };

  const selectCls =
    'text-sm bg-dark-card border border-dark-border rounded-lg px-3 py-1.5 text-text-secondary focus:outline-none focus:border-primary';

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between gap-3 flex-wrap mb-4">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">{t('title')}</h1>
          <p className="text-sm text-text-secondary mt-0.5">{t('subtitle')}</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <select className={selectCls} value={pmFilter} onChange={(e) => setPmFilter(e.target.value)}>
            <option value="all">{t('filter.all_pm')}</option>
            {managers.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
          <select
            className={selectCls}
            value={alertFilter}
            onChange={(e) => setAlertFilter(e.target.value as AlertFilter)}
          >
            <option value="all">{t('filter.all_alert')}</option>
            <option value="urgent">{t('alert.urgent')}</option>
            <option value="watch">{t('alert.watch')}</option>
            <option value="normal">{t('alert.normal')}</option>
          </select>
          <button
            onClick={() => setForm({ open: true, project: null })}
            className="text-sm bg-primary text-white rounded-lg px-3 py-1.5 hover:bg-primary/90 transition-colors"
          >
            + {t('new_project')}
          </button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
        <SummaryCard label={t('summary.in_progress')} value={summary.inProgress} />
        <SummaryCard label={t('summary.urgent')} value={summary.urgent} bg="bg-status-lost-bg" text="text-status-lost" />
        <SummaryCard label={t('summary.watch')} value={summary.watch} bg="bg-status-negotiating-bg" text="text-status-negotiating" />
        <SummaryCard label={t('summary.delivered')} value={summary.delivered} />
      </div>

      {/* List */}
      {loading ? (
        <Skeleton rows={6} />
      ) : visible.length === 0 ? (
        <EmptyState message={t('no_projects')} />
      ) : (
        <div className="bg-dark-card border border-dark-border rounded-xl overflow-hidden">
          {/* Column headers — grid matches ProjectRow (incl. its 4px left accent) */}
          <div className="hidden sm:grid sm:grid-cols-[minmax(0,170px)_minmax(0,1fr)_96px_64px] gap-x-3 px-4 py-2 border-b border-dark-border border-l-4 border-l-transparent text-xs text-text-muted">
            <div className="pl-4">{t('column.project')}</div>
            <div>{t('column.progress')}</div>
            <div>{t('column.manager')}</div>
            <div className="text-right">{t('column.stale')}</div>
          </div>
          {visible.map((p) => (
            <ProjectRow key={p.id} project={p} onClick={setDetail} />
          ))}
        </div>
      )}

      {/* Detail */}
      {detail && (
        <ProjectDetail
          project={detail}
          onClose={() => setDetail(null)}
          onChanged={(updated) => {
            setDetail(updated);
            load();
          }}
          onEdit={(p) => {
            setDetail(null);
            setForm({ open: true, project: p });
          }}
          onDelete={(p) => {
            setDetail(null);
            setDeleteTarget(p);
          }}
        />
      )}

      {/* Create / edit form */}
      {form.open && (
        <ProjectFormModal
          project={form.project}
          managers={managers}
          onClose={() => setForm({ open: false, project: null })}
          onSaved={() => {
            setForm({ open: false, project: null });
            load();
          }}
        />
      )}

      {/* Delete confirmation */}
      {deleteTarget && (
        <>
          <div className="fixed inset-0 bg-black/50 z-50" onClick={() => setDeleteTarget(null)} />
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
            <div className="bg-dark-card border border-dark-border rounded-xl w-full max-w-sm pointer-events-auto shadow-xl p-5">
              <h3 className="text-base font-semibold text-text-primary mb-2">{t('delete_confirm.title')}</h3>
              <p className="text-sm text-text-secondary mb-5">
                {t('delete_confirm.message', { name: deleteTarget.customer_name })}
              </p>
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setDeleteTarget(null)}
                  className="px-4 py-2 text-sm text-text-muted hover:text-text-primary transition-colors"
                >
                  {t('actions.cancel')}
                </button>
                <button
                  onClick={handleDelete}
                  disabled={deleting}
                  className="px-4 py-2 text-sm bg-status-lost text-white rounded-lg hover:opacity-90 disabled:opacity-50 transition-colors"
                >
                  {deleting ? t('actions.saving') : t('actions.confirm_delete')}
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function SummaryCard({
  label,
  value,
  bg = 'bg-dark-card',
  text = 'text-text-primary',
}: {
  label: string;
  value: number;
  bg?: string;
  text?: string;
}) {
  return (
    <div className={`${bg} border border-dark-border rounded-xl p-4`}>
      <p className={`text-xs mb-1.5 ${text === 'text-text-primary' ? 'text-text-secondary' : text}`}>{label}</p>
      <p className={`text-2xl font-bold ${text}`}>{value}</p>
    </div>
  );
}
