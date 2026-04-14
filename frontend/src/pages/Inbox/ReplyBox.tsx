import { useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { messagesApi } from '@/services/messages';

interface Props {
  contactId: string;
  channel: string;
  onSent: () => void;
}

export default function ReplyBox({ contactId, channel, onSent }: Props) {
  const { t } = useTranslation('inbox');
  const [message, setMessage] = useState('');
  const [subject, setSubject] = useState('');
  const [sending, setSending] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;
    setSending(true);
    try {
      if (channel === 'email') {
        await messagesApi.sendEmail(contactId, subject, message);
      } else {
        await messagesApi.sendWhatsApp(contactId, message);
      }
      setMessage('');
      setSubject('');
      onSent();
    } catch { /* ignore */ }
    setSending(false);
  };

  return (
    <form onSubmit={handleSubmit} className="border-t border-dark-border p-3 space-y-2">
      {channel === 'email' && (
        <input
          className="input text-sm"
          placeholder={t('subject')}
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
        />
      )}
      <div className="flex gap-2">
        <input
          className="input flex-1 text-sm"
          placeholder={t('replyPlaceholder')}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <button
          type="submit"
          disabled={sending || !message.trim()}
          className="btn-primary text-sm px-4"
        >
          {t('send')}
        </button>
      </div>
    </form>
  );
}
