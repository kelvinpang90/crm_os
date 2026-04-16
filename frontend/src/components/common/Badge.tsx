import { useTranslation } from 'react-i18next';
import clsx from 'clsx';

const statusStyles: Record<string, { text: string; bg: string }> = {
  'lead':        { text: 'text-[#60a5fa]', bg: 'bg-[rgba(59,130,246,0.15)]' },
  'following':   { text: 'text-[#4ade80]', bg: 'bg-[rgba(34,197,94,0.15)]' },
  'negotiating': { text: 'text-[#fbbf24]', bg: 'bg-[rgba(245,158,11,0.15)]' },
  'won':         { text: 'text-[#a78bfa]', bg: 'bg-[rgba(139,92,246,0.15)]' },
  'lost':        { text: 'text-[#f87171]', bg: 'bg-[rgba(239,68,68,0.15)]' },
};

const priorityStyles: Record<string, { text: string; bg: string }> = {
  'high': { text: 'text-[#f87171]', bg: 'bg-[rgba(239,68,68,0.15)]' },
  'mid':  { text: 'text-[#fbbf24]', bg: 'bg-[rgba(245,158,11,0.15)]' },
  'low':  { text: 'text-[#60a5fa]', bg: 'bg-[rgba(59,130,246,0.15)]' },
};

interface BadgeProps {
  value: string;
  type?: 'status' | 'priority';
  size?: 'sm' | 'md';
}

export default function Badge({ value, type = 'status', size = 'sm' }: BadgeProps) {
  const { t } = useTranslation('common');
  const styles = type === 'priority' ? priorityStyles[value] : statusStyles[value];
  const fallback = { text: 'text-text-secondary', bg: 'bg-dark-hover' };
  const s = styles || fallback;

  const label = type === 'status'
    ? t(`statusLabels.${value}`, { defaultValue: value })
    : t(`priorityLabels.${value}`, { defaultValue: value });

  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full font-medium',
        s.text, s.bg,
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm'
      )}
    >
      {label}
    </span>
  );
}
