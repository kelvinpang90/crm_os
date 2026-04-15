import { useTranslation } from 'react-i18next';
import clsx from 'clsx';

const statusStyles: Record<string, { text: string; bg: string }> = {
  '潜在客户': { text: 'text-[#60a5fa]', bg: 'bg-[rgba(59,130,246,0.15)]' },
  '跟进中': { text: 'text-[#4ade80]', bg: 'bg-[rgba(34,197,94,0.15)]' },
  '谈判中': { text: 'text-[#fbbf24]', bg: 'bg-[rgba(245,158,11,0.15)]' },
  '已成交': { text: 'text-[#a78bfa]', bg: 'bg-[rgba(139,92,246,0.15)]' },
  '已流失': { text: 'text-[#f87171]', bg: 'bg-[rgba(239,68,68,0.15)]' },
};

const priorityStyles: Record<string, { text: string; bg: string }> = {
  'high': { text: 'text-[#f87171]', bg: 'bg-[rgba(239,68,68,0.15)]' },
  'mid': { text: 'text-[#fbbf24]', bg: 'bg-[rgba(245,158,11,0.15)]' },
  'low': { text: 'text-[#60a5fa]', bg: 'bg-[rgba(59,130,246,0.15)]' },
};

interface BadgeProps {
  value: string;
  type?: 'status' | 'priority';
  size?: 'sm' | 'md';
}

export default function Badge({ value, type = 'status', size = 'sm' }: BadgeProps) {
  const { t } = useTranslation();
  const styles = type === 'priority' ? priorityStyles[value] : statusStyles[value];
  const fallback = { text: 'text-text-secondary', bg: 'bg-dark-hover' };
  const s = styles || fallback;

  const label = type === 'status'
    ? t(`statusLabels.${value}`, value)
    : value;

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
