import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { messagesApi } from '@/services/messages';
import type { Message } from '@/types';
import dayjs from 'dayjs';
import ReplyBox from './ReplyBox';

interface Props {
  contactId: string;
  contactName: string;
  channel: string;
}

export default function ConversationView({ contactId, contactName, channel }: Props) {
  const { t } = useTranslation('inbox');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const res = await messagesApi.getContactMessages(contactId);
      setMessages(res.data.data);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { load(); }, [contactId]);

  const handleSent = () => load();

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b border-dark-border">
        <h3 className="text-sm font-semibold text-text-primary">{contactName}</h3>
        <p className="text-xs text-text-muted">{t('conversation')} · {channel}</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {loading ? (
          <p className="text-text-muted text-sm text-center py-4">...</p>
        ) : messages.length === 0 ? (
          <p className="text-text-muted text-sm text-center py-4">{t('noMessages')}</p>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.direction === 'outbound' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[75%] rounded-xl px-3 py-2 ${
                msg.direction === 'outbound'
                  ? 'bg-primary/20 text-text-primary'
                  : 'bg-dark-hover text-text-primary'
              }`}>
                {msg.subject && (
                  <p className="text-xs font-medium text-text-secondary mb-1">{msg.subject}</p>
                )}
                <p className="text-sm whitespace-pre-wrap break-words">{msg.body}</p>
                <p className="text-[10px] text-text-muted mt-1 text-right">
                  {dayjs(msg.created_at).format('HH:mm')}
                </p>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Reply */}
      <ReplyBox contactId={contactId} channel={channel} onSent={handleSent} />
    </div>
  );
}
