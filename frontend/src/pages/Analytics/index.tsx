import { useTranslation } from 'react-i18next';

export default function AnalyticsPage() {
  const { t } = useTranslation();
  return (
    <div>
      <h1 className="text-2xl font-bold text-text-primary">{t('nav.analytics')}</h1>
      <p className="mt-2 text-text-secondary">Analytics charts coming soon...</p>
    </div>
  );
}
