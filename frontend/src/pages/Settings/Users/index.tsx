import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { usersApi } from '@/services/users';
import type { User } from '@/types';
import Modal from '@/components/common/Modal';
import UserForm from './UserForm';

export default function UsersPage() {
  const { t } = useTranslation('settings');
  const tc = useTranslation().t;
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = await usersApi.getAllUsers();
      setUsers(res.data.data);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const managers = users.filter((u) => u.role === 'admin' || u.role === 'manager');

  const handleToggle = async (userId: string) => {
    try {
      await usersApi.toggleUser(userId);
      load();
    } catch { /* ignore */ }
  };

  const handleSaved = () => {
    setShowForm(false);
    setEditing(null);
    load();
  };

  const ROLE_COLORS: Record<string, string> = {
    admin: 'bg-red-500/10 text-red-400',
    manager: 'bg-purple-500/10 text-purple-400',
    sales: 'bg-blue-500/10 text-blue-400',
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-text-primary">{t('userManagement.title')}</h2>
        <button
          onClick={() => { setEditing(null); setShowForm(true); }}
          className="btn-primary text-sm px-4 py-2"
        >
          {t('userManagement.newUser')}
        </button>
      </div>

      {loading ? (
        <div className="animate-pulse space-y-3">
          {[1, 2, 3].map((i) => <div key={i} className="h-14 bg-dark-card rounded-lg" />)}
        </div>
      ) : (
        <div className="bg-dark-card border border-dark-border rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-text-muted border-b border-dark-border">
                <th className="text-left py-3 px-4">{tc('name')}</th>
                <th className="text-left py-3 px-4">{tc('email')}</th>
                <th className="text-left py-3 px-4">{t('userManagement.role')}</th>
                <th className="text-center py-3 px-4">{tc('status')}</th>
                <th className="text-right py-3 px-4">{tc('actions')}</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-b border-dark-border/50 hover:bg-dark-hover">
                  <td className="py-3 px-4 text-text-primary font-medium">{user.name}</td>
                  <td className="py-3 px-4 text-text-secondary">{user.email}</td>
                  <td className="py-3 px-4">
                    <span className={`text-xs px-2 py-0.5 rounded ${ROLE_COLORS[user.role] || ''}`}>
                      {t(`userManagement.${user.role}`)}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <button
                      onClick={() => handleToggle(user.id)}
                      className={`text-xs px-2 py-0.5 rounded cursor-pointer ${
                        user.is_active
                          ? 'bg-green-500/10 text-green-400'
                          : 'bg-red-500/10 text-red-400'
                      }`}
                    >
                      {user.is_active ? t('userManagement.active') : t('userManagement.inactive')}
                    </button>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => { setEditing(user); setShowForm(true); }}
                      className="text-primary hover:text-primary/80 text-xs"
                    >
                      {tc('edit')}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal
        open={showForm}
        onClose={() => { setShowForm(false); setEditing(null); }}
        title={editing ? t('userManagement.editUser') : t('userManagement.newUser')}
      >
        <UserForm
          user={editing}
          managers={managers}
          onSaved={handleSaved}
          onCancel={() => { setShowForm(false); setEditing(null); }}
        />
      </Modal>
    </div>
  );
}
