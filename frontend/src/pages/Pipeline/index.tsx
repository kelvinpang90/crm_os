import { useTranslation } from 'react-i18next';

export default function PipelinePage() {
  const { t } = useTranslation();
  return (
    <div>
      <h1 className="text-2xl font-bold text-text-primary">{t('nav.pipeline')}</h1>
      <p className="mt-2 text-text-secondary">Pipeline board coming soon...</p>
    </div>
  );
}
