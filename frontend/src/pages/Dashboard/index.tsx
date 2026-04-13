import { useTranslation } from 'react-i18next';
import { useAuthStore } from '@/store/authStore';
import AdminDashboard from './AdminDashboard';
import ManagerDashboard from './ManagerDashboard';
import SalesDashboard from './SalesDashboard';

export default function DashboardPage() {
  const { t } = useTranslation('dashboard');
  const { user } = useAuthStore();

  return (
    <div>
      <h1 className="text-2xl font-bold text-text-primary mb-4">{t('title')}</h1>
      {user?.role === 'admin' && <AdminDashboard />}
      {user?.role === 'manager' && <ManagerDashboard />}
      {user?.role === 'sales' && <SalesDashboard />}
    </div>
  );
}
