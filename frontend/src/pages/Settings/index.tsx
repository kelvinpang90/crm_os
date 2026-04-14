import { Routes, Route, NavLink, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { usePermission } from '@/hooks/usePermission';
import { lazy, Suspense } from 'react';

const RoutingPage = lazy(() => import('./Routing'));
const UsersPage = lazy(() => import('./Users'));
const TargetsPage = lazy(() => import('./Targets'));
const IntegrationsPage = lazy(() => import('./Integrations'));
const IndustriesPage = lazy(() => import('./Industries'));

const NAV_ITEMS = [
  { path: 'routing', labelKey: 'routing' },
  { path: 'users', labelKey: 'users' },
  { path: 'targets', labelKey: 'targets' },
  { path: 'integrations', labelKey: 'integrations' },
  { path: 'industries', labelKey: 'industries' },
];

export default function SettingsPage() {
  const { t } = useTranslation('settings');
  const { canManageSettings } = usePermission();

  if (!canManageSettings) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-text-primary mb-4">{t('title')}</h1>
      <div className="flex gap-6">
        {/* Sidebar nav */}
        <nav className="w-48 shrink-0 space-y-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `block px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-primary/10 text-primary font-medium'
                    : 'text-text-secondary hover:bg-dark-hover hover:text-text-primary'
                }`
              }
            >
              {t(item.labelKey)}
            </NavLink>
          ))}
        </nav>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <Suspense fallback={<div className="animate-pulse h-32 bg-dark-card rounded-xl" />}>
            <Routes>
              <Route index element={<Navigate to="routing" replace />} />
              <Route path="routing" element={<RoutingPage />} />
              <Route path="users" element={<UsersPage />} />
              <Route path="targets" element={<TargetsPage />} />
              <Route path="integrations" element={<IntegrationsPage />} />
              <Route path="industries" element={<IndustriesPage />} />
            </Routes>
          </Suspense>
        </div>
      </div>
    </div>
  );
}
