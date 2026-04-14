import { useState, useEffect, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { usersApi } from '@/services/users';
import type { User } from '@/types';

interface Props {
  user?: User | null;
  managers: User[];
  onSaved: () => void;
  onCancel: () => void;
}

export default function UserForm({ user, managers, onSaved, onCancel }: Props) {
  const { t } = useTranslation('settings');
  const tc = useTranslation().t;
  const isEdit = !!user;

  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<string>(user?.role || 'sales');
  const [managerId, setManagerId] = useState(user?.manager_id || '');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !email.trim()) return;
    setSaving(true);
    try {
      if (isEdit && user) {
        const data: Record<string, unknown> = { name, email, role, manager_id: managerId || null };
        if (password) data.password = password;
        await usersApi.updateUser(user.id, data);
      } else {
        if (!password) return;
        await usersApi.createUser({ name, email, password, role, manager_id: managerId || undefined });
      }
      onSaved();
    } catch { /* ignore */ }
    setSaving(false);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm text-text-secondary mb-1">{tc('name')}</label>
        <input className="input w-full" value={name} onChange={(e) => setName(e.target.value)} required />
      </div>
      <div>
        <label className="block text-sm text-text-secondary mb-1">{tc('email')}</label>
        <input className="input w-full" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      </div>
      <div>
        <label className="block text-sm text-text-secondary mb-1">
          {tc('password')}{isEdit && ' (留空则不修改)'}
        </label>
        <input
          className="input w-full"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required={!isEdit}
          minLength={6}
        />
      </div>
      <div>
        <label className="block text-sm text-text-secondary mb-1">{t('userManagement.role')}</label>
        <select className="input w-full" value={role} onChange={(e) => setRole(e.target.value)}>
          <option value="admin">{t('userManagement.admin')}</option>
          <option value="manager">{t('userManagement.manager')}</option>
          <option value="sales">{t('userManagement.sales')}</option>
        </select>
      </div>
      <div>
        <label className="block text-sm text-text-secondary mb-1">{t('userManagement.manager_label')}</label>
        <select className="input w-full" value={managerId} onChange={(e) => setManagerId(e.target.value)}>
          <option value="">--</option>
          {managers.map((m) => (
            <option key={m.id} value={m.id}>{m.name}</option>
          ))}
        </select>
      </div>
      <div className="flex justify-end gap-3 pt-2">
        <button type="button" onClick={onCancel} className="btn-secondary text-sm px-4 py-2">
          {tc('cancel')}
        </button>
        <button type="submit" disabled={saving} className="btn-primary text-sm px-4 py-2">
          {tc('save')}
        </button>
      </div>
    </form>
  );
}
