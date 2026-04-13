import { useTranslation } from 'react-i18next';
import type { LeaderboardEntry } from '@/services/dashboard';

interface Props {
  entries: LeaderboardEntry[];
  title?: string;
  month: string;
  onMonthChange: (month: string) => void;
}

const RANK_BADGES = ['', '🥇', '🥈', '🥉'];

export default function LeaderboardTable({ entries, title, month, onMonthChange }: Props) {
  const { t } = useTranslation('dashboard');

  return (
    <div className="bg-dark-card border border-dark-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        {title && <h3 className="text-sm font-semibold text-text-primary">{title}</h3>}
        <input
          type="month"
          value={month}
          onChange={(e) => onMonthChange(e.target.value)}
          className="input text-xs w-auto py-1 px-2"
        />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-dark-border text-text-muted text-left">
              <th className="pb-2 font-medium">{t('rank')}</th>
              <th className="pb-2 font-medium">{t('salesName')}</th>
              <th className="pb-2 font-medium text-right">{t('dealAmount')}</th>
              <th className="pb-2 font-medium text-right">{t('dealCount')}</th>
              <th className="pb-2 font-medium text-right">{t('winRate')}</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e) => (
              <tr key={e.user_id} className="border-b border-dark-border/50 hover:bg-dark-hover">
                <td className="py-2 text-text-primary">
                  {RANK_BADGES[e.rank] || e.rank}
                </td>
                <td className="py-2">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white text-[10px] font-bold shrink-0">
                      {e.user_name.charAt(0)}
                    </div>
                    <span className="text-text-primary">{e.user_name}</span>
                  </div>
                </td>
                <td className="py-2 text-right text-text-primary">
                  ¥{e.deal_amount >= 10000
                    ? `${(e.deal_amount / 10000).toFixed(1)}万`
                    : e.deal_amount.toLocaleString()}
                </td>
                <td className="py-2 text-right text-text-secondary">{e.deal_count}</td>
                <td className="py-2 text-right text-text-secondary">{e.win_rate}%</td>
              </tr>
            ))}
            {entries.length === 0 && (
              <tr>
                <td colSpan={5} className="py-4 text-center text-text-muted">--</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
