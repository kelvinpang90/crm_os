import { useAuthStore } from '@/store/authStore';

export function usePermission() {
  const { user } = useAuthStore();
  const role = user?.role;

  return {
    isAdmin: role === 'admin',
    isManager: role === 'manager',
    isSales: role === 'sales',
    canDelete: role === 'admin',
    canManageSettings: role === 'admin',
    canViewTeam: role === 'admin' || role === 'manager',
  };
}
