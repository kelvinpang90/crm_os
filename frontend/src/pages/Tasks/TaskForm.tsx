import { useState, useEffect, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { usersApi } from '@/services/users';
import { contactsApi } from '@/services/contacts';
import type { Task, User, Contact } from '@/types';
import { useAuthStore } from '@/store/authStore';

interface Props {
  initial?: Partial<Task>;
  onSubmit: (data: Record<string, unknown>) => Promise<void>;
  submitting?: boolean;
}

export default function TaskForm({ initial, onSubmit, submitting }: Props) {
  const { t } = useTranslation('tasks');
  const { t: tc } = useTranslation('common');
  const { user: currentUser } = useAuthStore();

  const [form, setForm] = useState({
    title: initial?.title || '',
    contact_id: initial?.contact_id || '',
    assigned_to: initial?.assigned_to || currentUser?.id || '',
    priority: initial?.priority || '中',
    due_date: initial?.due_date || '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [users, setUsers] = useState<User[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);

  useEffect(() => {
    usersApi.getUsers().then((res) => setUsers(res.data.data)).catch(() => {});
    contactsApi.getContacts({ page: 1, page_size: 200 })
      .then((res) => setContacts(res.data.data.data))
      .catch(() => {});
  }, []);

  const set = (key: string, value: string) => {
    setForm((p) => ({ ...p, [key]: value }));
    if (errors[key]) setErrors((p) => { const n = { ...p }; delete n[key]; return n; });
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const errs: Record<string, string> = {};
    if (!form.title.trim()) errs.title = tc('required');
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;

    await onSubmit({
      title: form.title.trim(),
      contact_id: form.contact_id || null,
      assigned_to: form.assigned_to || null,
      priority: form.priority,
      due_date: form.due_date || null,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Title */}
      <div>
        <label className="block text-sm font-medium text-text-secondary mb-1">
          {t('taskTitle')} *
        </label>
        <input
          className="input"
          value={form.title}
          onChange={(e) => set('title', e.target.value)}
        />
        {errors.title && <p className="mt-1 text-xs text-red-400">{errors.title}</p>}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Related Contact */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            {t('relatedContact')}
          </label>
          <select
            className="input"
            value={form.contact_id}
            onChange={(e) => set('contact_id', e.target.value)}
          >
            <option value="">--</option>
            {contacts.map((c) => (
              <option key={c.id} value={c.id}>{c.name}{c.company ? ` (${c.company})` : ''}</option>
            ))}
          </select>
        </div>

        {/* Assignee */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            {t('assignee')}
          </label>
          <select
            className="input"
            value={form.assigned_to}
            onChange={(e) => set('assigned_to', e.target.value)}
          >
            <option value="">--</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>{u.name}</option>
            ))}
          </select>
        </div>

        {/* Priority */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            {tc('priority')}
          </label>
          <select
            className="input"
            value={form.priority}
            onChange={(e) => set('priority', e.target.value)}
          >
            {['高', '中', '低'].map((v) => (
              <option key={v} value={v}>{v}</option>
            ))}
          </select>
        </div>

        {/* Due Date */}
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-1">
            {t('dueDate')}
          </label>
          <input
            type="date"
            className="input"
            value={form.due_date}
            onChange={(e) => set('due_date', e.target.value)}
          />
        </div>
      </div>

      <button type="submit" disabled={submitting} className="btn-primary w-full h-11">
        {submitting ? '...' : tc('save')}
      </button>
    </form>
  );
}
