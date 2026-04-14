import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { salesTargetsApi, type SalesTargetItem } from '@/services/analytics';
import { usersApi } from '@/services/users';
import type { User } from '@/types';
import Modal from '@/components/common/Modal';

const currentYear = new Date().getFullYear();

export default function TargetsPage() {
  const { t } = useTranslation('settings');
  const tc = useTranslation().t;
  const [targets, setTargets] = useState<SalesTargetItem[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [year, setYear] = useState(currentYear);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  // Form state
  const [formUserId, setFormUserId] = useState('');
  const [formMonth, setFormMonth] = useState(1);
  const [formAmount, setFormAmount] = useState(0);
  const [formCount, setFormCount] = useState(0);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [tRes, uRes] = await Promise.all([
        salesTargetsApi.getTargets({ year }),
        usersApi.getUsers(),
      ]);
      setTargets(tRes.data.data);
      setUsers(uRes.data.data.filter((u: User) => u.role === 'sales' && u.is_active));
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { load(); }, [year]);

  const handleCreate = async () => {
    if (!formUserId) return;
    setSaving(true);
    try {
      await salesTargetsApi.createTarget({
        user_id: formUserId,
        year,
        month: formMonth,
        target_amount: formAmount,
        target_count: formCount,
      });
      setShowForm(false);
      load();
    } catch { /* ignore */ }
    setSaving(false);
  };

  const handleDelete = async (id: string) => {
    if (!confirm(tc('deleteConfirm'))) return;
    try {
      await salesTargetsApi.deleteTarget(id);
      load();
    } catch { /* ignore */ }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-text-primary">{t('salesTargets.title')}</h2>
        <div className="flex items-center gap-3">
          <select
            className="input text-sm"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
          >
            {[currentYear - 1, currentYear, currentYear + 1].map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
          <button onClick={() => setShowForm(true)} className="btn-primary text-sm px-4 py-2">
            {tc('create')}
          </button>
        </div>
      </div>

      {loading ? (
        <div className="animate-pulse space-y-3">
          {[1, 2, 3].map((i) => <div key={i} className="h-14 bg-dark-card rounded-lg" />)}
        </div>
      ) : targets.length === 0 ? (
        <p className="text-text-muted text-sm text-center py-8">{tc('noData')}</p>
      ) : (
        <div className="bg-dark-card border border-dark-border rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-text-muted border-b border-dark-border">
                <th className="text-left py-3 px-4">销售</th>
                <th className="text-center py-3 px-4">{t('salesTargets.month')}</th>
                <th className="text-right py-3 px-4">{t('salesTargets.targetAmount')}</th>
                <th className="text-right py-3 px-4">{t('salesTargets.targetCount')}</th>
                <th className="text-right py-3 px-4">{tc('actions')}</th>
              </tr>
            </thead>
            <tbody>
              {targets.map((tgt) => (
                <tr key={tgt.id} className="border-b border-dark-border/50 hover:bg-dark-hover">
                  <td className="py-3 px-4 text-text-primary">{tgt.user_name || tgt.user_id}</td>
                  <td className="py-3 px-4 text-center text-text-secondary">{tgt.month}月</td>
                  <td className="py-3 px-4 text-right text-text-secondary">
                    ¥{tgt.target_amount.toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-right text-text-secondary">{tgt.target_count}</td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => handleDelete(tgt.id)}
                      className="text-red-400 hover:text-red-300 text-xs"
                    >
                      {tc('delete')}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={showForm} onClose={() => setShowForm(false)} title={t('salesTargets.title')}>
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-text-secondary mb-1">销售</label>
            <select className="input w-full" value={formUserId} onChange={(e) => setFormUserId(e.target.value)}>
              <option value="">-- 选择销售 --</option>
              {users.map((u) => (
                <option key={u.id} value={u.id}>{u.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-text-secondary mb-1">{t('salesTargets.month')}</label>
            <select className="input w-full" value={formMonth} onChange={(e) => setFormMonth(Number(e.target.value))}>
              {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                <option key={m} value={m}>{m}月</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-text-secondary mb-1">{t('salesTargets.targetAmount')}</label>
            <input
              className="input w-full"
              type="number"
              min={0}
              value={formAmount}
              onChange={(e) => setFormAmount(Number(e.target.value))}
            />
          </div>
          <div>
            <label className="block text-sm text-text-secondary mb-1">{t('salesTargets.targetCount')}</label>
            <input
              className="input w-full"
              type="number"
              min={0}
              value={formCount}
              onChange={(e) => setFormCount(Number(e.target.value))}
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button onClick={() => setShowForm(false)} className="btn-secondary text-sm px-4 py-2">
              {tc('cancel')}
            </button>
            <button onClick={handleCreate} disabled={saving || !formUserId} className="btn-primary text-sm px-4 py-2">
              {tc('save')}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
