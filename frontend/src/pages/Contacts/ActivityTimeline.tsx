import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { contactsApi } from '@/services/contacts';
import type { Activity } from '@/types';
import dayjs from 'dayjs';

interface Props {
  contactId: string;
}

const typeColors: Record<string, string> = {
  'phone': 'bg-blue-500',
  'email': 'bg-green-500',
  'meeting': 'bg-purple-500',
  'WhatsApp': 'bg-emerald-500',
  'other': 'bg-gray-500',
  'status change': 'bg-yellow-500',
};

export default function ActivityTimeline({ contactId }: Props) {
  const { t } = useTranslation('contacts');
  const [activities, setActivities] = useState<Activity[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [formType, setFormType] = useState('phone');
  const [formContent, setFormContent] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const load = async () => {
    try {
      const res = await contactsApi.getActivities(contactId);
      setActivities(res.data.data || []);
    } catch { /* ignore */ }
  };

  useEffect(() => { load(); }, [contactId]);

  const handleSubmit = async () => {
    if (!formContent.trim()) return;
    setSubmitting(true);
    try {
      await contactsApi.createActivity(contactId, { type: formType, content: formContent });
      setFormContent('');
      setShowForm(false);
      load();
    } catch { /* ignore */ }
    setSubmitting(false);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold text-text-primary">{t('followHistory')}</h4>
        <button onClick={() => setShowForm(!showForm)} className="text-xs text-primary hover:underline">
          {showForm ? t('common:cancel') : `+ ${t('followUp')}`}
        </button>
      </div>

      {showForm && (
        <div className="card p-3 mb-4 space-y-2">
          <select value={formType} onChange={(e) => setFormType(e.target.value)} className="input text-sm">
            {['phone', 'email', 'meeting', 'WhatsApp', 'other'].map((v) => (
              <option key={v} value={v}>{t(`followTypes.${v}`)}</option>
            ))}
          </select>
          <textarea
            className="input text-sm min-h-[60px]"
            placeholder={t('followContent')}
            value={formContent}
            onChange={(e) => setFormContent(e.target.value)}
          />
          <button onClick={handleSubmit} disabled={submitting} className="btn-primary text-xs px-3 py-1">
            {submitting ? '...' : t('common:submit')}
          </button>
        </div>
      )}

      <div className="space-y-0">
        {activities.map((a, i) => (
          <div key={a.id} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div className={`w-2.5 h-2.5 rounded-full mt-1.5 ${typeColors[a.type] || 'bg-gray-500'}`} />
              {i < activities.length - 1 && <div className="w-px flex-1 bg-dark-border" />}
            </div>
            <div className="pb-4 min-w-0 flex-1">
              <div className="flex items-center gap-2 text-xs text-text-muted">
                <span className="font-medium text-text-secondary">{a.user_name}</span>
                <span>{t(`followTypes.${a.type}`, a.type)}</span>
                <span>{dayjs(a.follow_date).format('MM-DD HH:mm')}</span>
              </div>
              {a.content && <p className="mt-1 text-sm text-text-secondary">{a.content}</p>}
            </div>
          </div>
        ))}
        {activities.length === 0 && (
          <p className="text-xs text-text-muted text-center py-4">{t('common:noData')}</p>
        )}
      </div>
    </div>
  );
}
