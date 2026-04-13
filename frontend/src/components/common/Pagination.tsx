import { useTranslation } from 'react-i18next';

interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onChange: (page: number) => void;
}

export default function Pagination({ page, pageSize, total, onChange }: PaginationProps) {
  const { t } = useTranslation();
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="flex items-center justify-between py-3 text-sm text-text-secondary">
      <span>{t('total', { count: total })}</span>
      <div className="flex items-center gap-2">
        <button
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
          className="px-3 py-1 rounded-lg border border-dark-border hover:bg-dark-hover disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          &lt;
        </button>
        <span>{t('page', { current: page, total: totalPages })}</span>
        <button
          disabled={page >= totalPages}
          onClick={() => onChange(page + 1)}
          className="px-3 py-1 rounded-lg border border-dark-border hover:bg-dark-hover disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          &gt;
        </button>
      </div>
    </div>
  );
}
