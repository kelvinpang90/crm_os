import { useTranslation } from 'react-i18next';

export default function TasksPage() {
  const { t } = useTranslation('tasks');
  return (
    <div>
      <h1 className="text-2xl font-bold text-text-primary">{t('title')}</h1>
      <p className="mt-2 text-text-secondary">Tasks center coming soon...</p>
    </div>
  );
}
