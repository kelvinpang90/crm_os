import { useTranslation } from 'react-i18next';
import dayjs from 'dayjs';
import type { Message } from '@/types';

interface Props {
  messages: Message[];
  selectedId?: string;
  onSelect: (msg: Message) => void;
}

const CHANNEL_ICONS: Record<string, string> = {
  whatsapp: '💬',
  email: '📧',
};

export default function MessageList({ messages, selectedId, onSelect }: Props) {
  const { t } = useTranslation('inbox');

  return (
    <div className="space-y-1">
      {messages.map((msg) => (
        <button
          key={msg.id}
          onClick={() => onSelect(msg)}
          className={`w-full text-left p-3 rounded-lg border transition-colors ${
            selectedId === msg.id
              ? 'border-primary/50 bg-primary/5'
              : 'border-dark-border hover:bg-dark-hover'
          }`}
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm">{CHANNEL_ICONS[msg.channel] || '💬'}</span>
            <span className={`text-sm font-medium truncate ${msg.is_read ? 'text-text-secondary' : 'text-text-primary'}`}>
              {msg.contact_name || msg.sender_id}
            </span>
            {!msg.is_read && (
              <span className="w-2 h-2 rounded-full bg-primary shrink-0" />
            )}
            <span className="text-xs text-text-muted ml-auto shrink-0">
              {dayjs(msg.created_at).format('MM/DD HH:mm')}
            </span>
          </div>
          {msg.subject && (
            <p className="text-xs text-text-secondary truncate mb-0.5">{msg.subject}</p>
          )}
          <p className="text-xs text-text-muted truncate">{msg.body}</p>
          <div className="flex items-center gap-2 mt-1">
            <span className={`text-[10px] px-1.5 py-0.5 rounded ${
              msg.direction === 'inbound' ? 'bg-blue-500/10 text-blue-400' : 'bg-green-500/10 text-green-400'
            }`}>
              {t(msg.direction)}
            </span>
          </div>
        </button>
      ))}
    </div>
  );
}
