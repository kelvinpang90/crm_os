import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { routingApi } from '@/services/routing';
import type { RoutingRule } from '@/types';
import RoutingRuleForm from './RoutingRuleForm';
import Modal from '@/components/common/Modal';
import EmptyState from '@/components/common/EmptyState';
import Skeleton from '@/components/common/Skeleton';

const STRATEGY_COLORS: Record<string, string> = {
  workload: 'bg-blue-500/10 text-blue-400',
  region: 'bg-green-500/10 text-green-400',
  win_rate: 'bg-purple-500/10 text-purple-400',
};

export default function RoutingPage() {
  const { t } = useTranslation('settings');
  const { t: tc } = useTranslation('common');

  const [rules, setRules] = useState<RoutingRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [editing, setEditing] = useState<RoutingRule | null>(null);
  const [deleting, setDeleting] = useState<RoutingRule | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await routingApi.getRules();
      setRules(res.data.data);
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleCreate = async (data: Record<string, unknown>) => {
    setSubmitting(true);
    try {
      await routingApi.createRule(data as any);
      setShowCreate(false);
      load();
    } catch { /* ignore */ }
    setSubmitting(false);
  };

  const handleUpdate = async (data: Record<string, unknown>) => {
    if (!editing) return;
    setSubmitting(true);
    try {
      await routingApi.updateRule(editing.id, data as any);
      setEditing(null);
      load();
    } catch { /* ignore */ }
    setSubmitting(false);
  };

  const handleDelete = async () => {
    if (!deleting) return;
    try {
      await routingApi.deleteRule(deleting.id);
      setDeleting(null);
      load();
    } catch { /* ignore */ }
  };

  const handleToggle = async (id: string) => {
    try {
      await routingApi.toggleRule(id);
      load();
    } catch { /* ignore */ }
  };

  const strategyLabel = (s: string) => {
    const map: Record<string, string> = {
      workload: t('routingRules.workload'),
      region: t('routingRules.region'),
      win_rate: t('routingRules.winRate'),
    };
    return map[s] || s;
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-text-primary">{t('routingRules.title')}</h2>
        <button onClick={() => setShowCreate(true)} className="btn-primary text-sm">
          + {t('routingRules.newRule')}
        </button>
      </div>

      {loading ? (
        <Skeleton rows={4} />
      ) : rules.length === 0 ? (
        <EmptyState message={t('routingRules.title')} />
      ) : (
        <div className="space-y-2">
          {rules.map((rule) => (
            <div
              key={rule.id}
              className="flex items-center gap-4 p-3 bg-dark-card border border-dark-border rounded-lg hover:bg-dark-hover transition-colors"
            >
              {/* Toggle */}
              <button
                onClick={() => handleToggle(rule.id)}
                className={`relative w-9 h-5 rounded-full transition-colors shrink-0 ${
                  rule.is_active ? 'bg-primary' : 'bg-dark-border'
                }`}
              >
                <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                  rule.is_active ? 'left-4' : 'left-0.5'
                }`} />
              </button>

              {/* Name + Strategy */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-medium ${rule.is_active ? 'text-text-primary' : 'text-text-muted'}`}>
                    {rule.name}
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${STRATEGY_COLORS[rule.strategy] || ''}`}>
                    {strategyLabel(rule.strategy)}
                  </span>
                </div>
                <p className="text-xs text-text-muted mt-0.5">
                  {tc('priority')}: {rule.priority} · {t('routingRules.targetUsers')}: {(rule.target_users || []).length}
                </p>
              </div>

              {/* Actions */}
              <div className="flex gap-1 shrink-0">
                <button
                  onClick={() => setEditing(rule)}
                  className="text-xs text-text-muted hover:text-text-primary px-2 py-1"
                >
                  {tc('edit')}
                </button>
                <button
                  onClick={() => setDeleting(rule)}
                  className="text-xs text-text-muted hover:text-red-400 px-2 py-1"
                >
                  {tc('delete')}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title={t('routingRules.newRule')} size="md">
        <RoutingRuleForm onSubmit={handleCreate} submitting={submitting} />
      </Modal>

      {/* Edit Modal */}
      <Modal open={!!editing} onClose={() => setEditing(null)} title={t('routingRules.ruleName')} size="md">
        {editing && (
          <RoutingRuleForm initial={editing} onSubmit={handleUpdate} submitting={submitting} />
        )}
      </Modal>

      {/* Delete Confirm */}
      <Modal open={!!deleting} onClose={() => setDeleting(null)} title={tc('delete')} size="sm">
        <p className="text-text-secondary mb-4">{tc('deleteConfirm')}</p>
        <div className="flex gap-2 justify-end">
          <button onClick={() => setDeleting(null)} className="btn-secondary text-sm">{tc('cancel')}</button>
          <button onClick={handleDelete} className="btn-primary text-sm bg-red-500 hover:bg-red-600">{tc('delete')}</button>
        </div>
      </Modal>
    </div>
  );
}
