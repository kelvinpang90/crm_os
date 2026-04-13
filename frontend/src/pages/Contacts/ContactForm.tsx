import { useState, type FormEvent, type KeyboardEvent } from 'react';
import { useTranslation } from 'react-i18next';
import type { Contact } from '@/types';

const INDUSTRIES = [
  '科技/IT', '金融/保险', '医疗/健康', '教育/培训', '零售/电商',
  '制造/工业', '房地产', '咨询/服务', '餐饮/酒店', '物流/供应链',
];
const STATUSES = ['潜在客户', '跟进中', '谈判中', '已成交', '已流失'];
const PRIORITIES = ['高', '中', '低'];

interface Props {
  initial?: Partial<Contact>;
  onSubmit: (data: Record<string, unknown>) => Promise<void>;
  submitting?: boolean;
}

export default function ContactForm({ initial, onSubmit, submitting }: Props) {
  const { t } = useTranslation('contacts');
  const [form, setForm] = useState({
    name: initial?.name || '',
    company: initial?.company || '',
    industry: initial?.industry || '',
    status: initial?.status || '潜在客户',
    priority: initial?.priority || '中',
    deal_value: initial?.deal_value?.toString() || '0',
    email: initial?.email || '',
    phone: initial?.phone || '',
    address: initial?.address || '',
    notes: initial?.notes || '',
    tags: initial?.tags || [] as string[],
  });
  const [tagInput, setTagInput] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const set = (key: string, value: unknown) => {
    setForm((p) => ({ ...p, [key]: value }));
    if (errors[key]) setErrors((p) => { const n = { ...p }; delete n[key]; return n; });
  };

  const validate = () => {
    const e: Record<string, string> = {};
    if (!form.name.trim()) e.name = t('common:required');
    if (form.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = t('common:invalidEmail');
    if (form.deal_value && Number(form.deal_value) < 0) e.deal_value = '必须为正数';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    await onSubmit({
      ...form,
      deal_value: parseFloat(form.deal_value) || 0,
      company: form.company || null,
      email: form.email || null,
      phone: form.phone || null,
      address: form.address || null,
      notes: form.notes || null,
    });
  };

  const addTag = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault();
      if (!form.tags.includes(tagInput.trim())) {
        set('tags', [...form.tags, tagInput.trim()]);
      }
      setTagInput('');
    }
  };

  const removeTag = (tag: string) => set('tags', form.tags.filter((t) => t !== tag));

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field label={`${t('common:name')} *`} error={errors.name}>
          <input className="input" value={form.name} onChange={(e) => set('name', e.target.value)} />
        </Field>
        <Field label={t('common:company')}>
          <input className="input" value={form.company} onChange={(e) => set('company', e.target.value)} />
        </Field>
        <Field label={t('common:industry')}>
          <select className="input" value={form.industry} onChange={(e) => set('industry', e.target.value)}>
            <option value="">--</option>
            {INDUSTRIES.map((v) => <option key={v} value={v}>{t(`industries.${v}`, v)}</option>)}
          </select>
        </Field>
        <Field label={t('common:status')}>
          <select className="input" value={form.status} onChange={(e) => set('status', e.target.value)}>
            {STATUSES.map((v) => <option key={v} value={v}>{t(`common:statusLabels.${v}`, v)}</option>)}
          </select>
        </Field>
        <Field label={t('common:priority')}>
          <select className="input" value={form.priority} onChange={(e) => set('priority', e.target.value)}>
            {PRIORITIES.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
        </Field>
        <Field label={t('dealValue')} error={errors.deal_value}>
          <input type="number" className="input" value={form.deal_value} onChange={(e) => set('deal_value', e.target.value)} />
        </Field>
        <Field label={t('common:email')} error={errors.email}>
          <input type="email" className="input" value={form.email} onChange={(e) => set('email', e.target.value)} />
        </Field>
        <Field label={t('common:phone')}>
          <input className="input" value={form.phone} onChange={(e) => set('phone', e.target.value)} />
        </Field>
      </div>

      <Field label={t('common:address')}>
        <input className="input" value={form.address} onChange={(e) => set('address', e.target.value)} />
      </Field>

      <Field label={t('common:notes')}>
        <textarea className="input min-h-[80px]" value={form.notes} onChange={(e) => set('notes', e.target.value)} />
      </Field>

      <Field label={t('common:tags')}>
        <div className="flex flex-wrap gap-1 mb-1">
          {form.tags.map((tag) => (
            <span key={tag} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-primary/15 text-primary">
              {tag}
              <button type="button" onClick={() => removeTag(tag)} className="hover:text-red-400">&times;</button>
            </span>
          ))}
        </div>
        <input
          className="input"
          placeholder="输入标签后按回车"
          value={tagInput}
          onChange={(e) => setTagInput(e.target.value)}
          onKeyDown={addTag}
        />
      </Field>

      <button type="submit" disabled={submitting} className="btn-primary w-full h-11">
        {submitting ? '...' : t('common:save')}
      </button>
    </form>
  );
}

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-sm font-medium text-text-secondary mb-1">{label}</label>
      {children}
      {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
    </div>
  );
}
