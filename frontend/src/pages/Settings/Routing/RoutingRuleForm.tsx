import { useState, useEffect, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { usersApi } from '@/services/users';
import type { User, RoutingRule } from '@/types';

interface Props {
  initial?: Partial<RoutingRule>;
  onSubmit: (data: Record<string, unknown>) => Promise<void>;
  submitting?: boolean;
}

export default function RoutingRuleForm({ initial, onSubmit, submitting }: Props) {
  const { t } = useTranslation('settings');
  const { t: tc } = useTranslation('common');

  const [form, setForm] = useState({
    name: initial?.name || '',
    strategy: initial?.strategy || 'workload',
    priority: initial?.priority ?? 0,
    is_active: initial?.is_active ?? true,
    target_users: (initial?.target_users || []) as string[],
    regionKeywords: ((initial?.conditions as any)?.keywords || []) as string[],
  });
  const [users, setUsers] = useState<User[]>([]);
  const [kwInput, setKwInput] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    usersApi.getUsers().then((res) => {
      setUsers(res.data.data.filter((u) => u.role === 'sales' && u.is_active));
    }).catch(() => {});
  }, []);

  const set = (key: string, value: unknown) => {
    setForm((p) => ({ ...p, [key]: value }));
    if (errors[key]) setErrors((p) => { const n = { ...p }; delete n[key]; return n; });
  };

  const toggleUser = (id: string) => {
    setForm((p) => ({
      ...p,
      target_users: p.target_users.includes(id)
        ? p.target_users.filter((u) => u !== id)
        : [...p.target_users, id],
    }));
  };

  const addKeyword = () => {
    const kw = kwInput.trim();
    if (kw && !form.regionKeywords.includes(kw)) {
      set('regionKeywords', [...form.regionKeywords, kw]);
    }
    setKwInput('');
  };

  const removeKeyword = (kw: string) => {
    set('regionKeywords', form.regionKeywords.filter((k) => k !== kw));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const errs: Record<string, string> = {};
    if (!form.name.trim()) errs.name = tc('required');
    if (form.target_users.length === 0) errs.target_users = tc('required');
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;

    const conditions = form.strategy === 'region'
      ? { keywords: form.regionKeywords }
      : null;

    await onSubmit({
      name: form.name.trim(),
      strategy: form.strategy,
      priority: form.priority,
      is_active: form.is_active,
      target_users: form.target_users,
      conditions,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Name */}
      <div>
        <label className="block text-sm font-medium text-text-secondary mb-1">
          {t('routingRules.ruleName')} *
        </label>
        <input className="input" value={form.name} onChange={(e) => set('name', e.target.value)} />
        {errors.name && <p className="mt-1 text-xs text-red-400">{errors.name}</p>}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Strategy */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            {t('routingRules.strategy')}
          </label>
          <select className="input" value={form.strategy} onChange={(e) => set('strategy', e.target.value)}>
            <option value="workload">{t('routingRules.workload')}</option>
            <option value="region">{t('routingRules.region')}</option>
            <option value="win_rate">{t('routingRules.winRate')}</option>
          </select>
        </div>

        {/* Priority */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            {tc('priority')}
          </label>
          <input
            type="number"
            className="input"
            value={form.priority}
            onChange={(e) => set('priority', parseInt(e.target.value) || 0)}
          />
        </div>
      </div>

      {/* Region conditions */}
      {form.strategy === 'region' && (
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            {t('routingRules.regionConditions')}
          </label>
          <div className="flex gap-2 mb-2">
            <input
              className="input flex-1"
              value={kwInput}
              onChange={(e) => setKwInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addKeyword(); } }}
              placeholder="输入关键词后按回车"
            />
            <button type="button" onClick={addKeyword} className="btn-secondary text-sm px-3">+</button>
          </div>
          <div className="flex flex-wrap gap-1">
            {form.regionKeywords.map((kw) => (
              <span
                key={kw}
                className="inline-flex items-center gap-1 px-2 py-0.5 bg-dark-hover text-text-secondary rounded text-xs"
              >
                {kw}
                <button type="button" onClick={() => removeKeyword(kw)} className="text-text-muted hover:text-red-400">×</button>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Target users */}
      <div>
        <label className="block text-sm font-medium text-text-secondary mb-1">
          {t('routingRules.targetUsers')} *
        </label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-40 overflow-y-auto border border-dark-border rounded-lg p-2">
          {users.map((u) => (
            <label key={u.id} className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer hover:text-text-primary">
              <input
                type="checkbox"
                checked={form.target_users.includes(u.id)}
                onChange={() => toggleUser(u.id)}
                className="rounded border-dark-border"
              />
              {u.name}
            </label>
          ))}
          {users.length === 0 && <p className="text-xs text-text-muted col-span-full">无可用销售</p>}
        </div>
        {errors.target_users && <p className="mt-1 text-xs text-red-400">{errors.target_users}</p>}
      </div>

      {/* Active toggle */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => set('is_active', !form.is_active)}
          className={`relative w-10 h-5 rounded-full transition-colors ${
            form.is_active ? 'bg-primary' : 'bg-dark-border'
          }`}
        >
          <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
            form.is_active ? 'left-5' : 'left-0.5'
          }`} />
        </button>
        <span className="text-sm text-text-secondary">
          {form.is_active ? t('routingRules.enabled') : t('routingRules.disabled')}
        </span>
      </div>

      <button type="submit" disabled={submitting} className="btn-primary w-full h-11">
        {submitting ? '...' : tc('save')}
      </button>
    </form>
  );
}
