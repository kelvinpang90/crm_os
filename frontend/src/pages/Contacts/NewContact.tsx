import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import ContactForm from './ContactForm';
import ExcelImport from './ExcelImport';
import { contactsApi } from '@/services/contacts';
import clsx from 'clsx';

export default function NewContactPage() {
  const { t } = useTranslation('contacts');
  const navigate = useNavigate();
  const [tab, setTab] = useState<'manual' | 'excel'>('manual');
  const [submitting, setSubmitting] = useState(false);

  const handleCreate = async (data: Record<string, unknown>) => {
    setSubmitting(true);
    try {
      await contactsApi.createContact(data as any);
      navigate('/contacts');
    } catch { /* ignore */ }
    setSubmitting(false);
  };

  return (
    <div className="max-w-3xl">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate('/contacts')} className="text-text-muted hover:text-text-primary">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="text-2xl font-bold text-text-primary">{t('newContact')}</h1>
      </div>

      {/* Tab */}
      <div className="flex gap-1 mb-6 border-b border-dark-border">
        {(['manual', 'excel'] as const).map((v) => (
          <button
            key={v}
            onClick={() => setTab(v)}
            className={clsx(
              'px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px',
              tab === v
                ? 'text-primary border-primary'
                : 'text-text-muted border-transparent hover:text-text-secondary'
            )}
          >
            {v === 'manual' ? t('manualEntry') : t('excelImport')}
          </button>
        ))}
      </div>

      <div className="card p-6">
        {tab === 'manual' ? (
          <ContactForm onSubmit={handleCreate} submitting={submitting} />
        ) : (
          <ExcelImport />
        )}
      </div>
    </div>
  );
}
