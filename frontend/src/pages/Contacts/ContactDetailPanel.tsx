import { useTranslation } from 'react-i18next';
import { useIsMobile } from '@/hooks/useBreakpoint';
import Badge from '@/components/common/Badge';
import ActivityTimeline from './ActivityTimeline';
import type { Contact } from '@/types';
import clsx from 'clsx';

interface Props {
  contact: Contact;
  onClose: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

export default function ContactDetailPanel({ contact, onClose, onEdit, onDelete }: Props) {
  const { t } = useTranslation('contacts');
  const isMobile = useIsMobile();

  return (
    <>
      <div className="fixed inset-0 bg-black/40 z-40" onClick={onClose} />
      <div className={clsx(
        'fixed top-0 right-0 h-full bg-dark-card border-l border-dark-border z-50 overflow-y-auto transition-transform',
        isMobile ? 'w-full' : 'w-96'
      )}>
        {/* Header */}
        <div className="sticky top-0 bg-dark-card border-b border-dark-border p-4 flex items-center justify-between">
          <h3 className="font-semibold text-text-primary">{t('contactDetail')}</h3>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-4 space-y-5">
          {/* Avatar + Name */}
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white text-lg font-bold shrink-0">
              {contact.name.charAt(0)}
            </div>
            <div>
              <h4 className="font-semibold text-text-primary">{contact.name}</h4>
              <p className="text-sm text-text-muted">{contact.company || '-'}</p>
            </div>
          </div>

          {/* Status & Priority */}
          <div className="flex items-center gap-2">
            <Badge value={contact.status} type="status" />
            <Badge value={contact.priority} type="priority" />
          </div>

          {/* Info Grid */}
          <div className="space-y-3 text-sm">
            <InfoRow label={t('common:industry')} value={contact.industry} />
            <InfoRow label={t('dealValue')} value={contact.deal_value ? `¥${Number(contact.deal_value).toLocaleString()}` : '-'} />
            <InfoRow label={t('common:email')} value={contact.email} />
            <InfoRow label={t('common:phone')} value={contact.phone} />
            <InfoRow label={t('common:address')} value={contact.address} />
            <InfoRow label={t('lastContact')} value={contact.last_contact} />
          </div>

          {/* Tags */}
          {contact.tags && contact.tags.length > 0 && (
            <div>
              <p className="text-xs text-text-muted mb-1">{t('common:tags')}</p>
              <div className="flex flex-wrap gap-1">
                {contact.tags.map((tag) => (
                  <span key={tag} className="px-2 py-0.5 rounded-full text-xs bg-dark-hover text-text-secondary">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Notes */}
          {contact.notes && (
            <div>
              <p className="text-xs text-text-muted mb-1">{t('common:notes')}</p>
              <p className="text-sm text-text-secondary">{contact.notes}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2">
            <button onClick={onEdit} className="btn-primary text-sm flex-1">
              {t('common:edit')}
            </button>
            <button onClick={onDelete} className="btn-secondary text-sm text-red-400 hover:text-red-300">
              {t('common:delete')}
            </button>
          </div>

          {/* Activity Timeline */}
          <div className="border-t border-dark-border pt-4">
            <ActivityTimeline contactId={contact.id} />
          </div>
        </div>
      </div>
    </>
  );
}

function InfoRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="flex justify-between">
      <span className="text-text-muted">{label}</span>
      <span className="text-text-secondary">{value || '-'}</span>
    </div>
  );
}
