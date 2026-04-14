import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { tasksApi, type TaskListParams } from '@/services/tasks';
import type { Task } from '@/types';
import TaskList from './TaskList';
import TaskForm from './TaskForm';
import Modal from '@/components/common/Modal';
import Pagination from '@/components/common/Pagination';
import EmptyState from '@/components/common/EmptyState';
import Skeleton from '@/components/common/Skeleton';
import clsx from 'clsx';
import toast from 'react-hot-toast';

const TABS = ['all', 'pending', 'today', 'overdue', 'done'] as const;

export default function TasksPage() {
  const { t } = useTranslation('tasks');
  const { t: tc } = useTranslation('common');

  const [tasks, setTasks] = useState<Task[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<string>('pending');
  const [params, setParams] = useState<TaskListParams>({ page: 1, page_size: 20, status: 'pending' });
  const [showCreate, setShowCreate] = useState(false);
  const [editing, setEditing] = useState<Task | null>(null);
  const [deleting, setDeleting] = useState<Task | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await tasksApi.getTasks(params);
      const d = res.data.data;
      setTasks(d.data);
      setTotal(d.total);
    } catch { /* ignore */ }
    setLoading(false);
  }, [params]);

  useEffect(() => { load(); }, [load]);

  // Today due reminder on first mount
  useEffect(() => {
    tasksApi.getTasks({ status: 'today', page: 1, page_size: 1 })
      .then((res) => {
        const count = res.data.data.total;
        if (count > 0) {
          toast(t('todayDueReminder', { count }), { icon: '⏰', duration: 5000 });
        }
      })
      .catch(() => {});
  }, [t]);

  const handleTabChange = (newTab: string) => {
    setTab(newTab);
    setParams((p) => ({
      ...p,
      status: newTab === 'all' ? undefined : newTab,
      page: 1,
    }));
  };

  const handleToggle = async (id: string) => {
    try {
      await tasksApi.toggleTask(id);
      load();
    } catch { /* ignore */ }
  };

  const handleCreate = async (data: Record<string, unknown>) => {
    setSubmitting(true);
    try {
      await tasksApi.createTask(data as any);
      setShowCreate(false);
      load();
    } catch { /* ignore */ }
    setSubmitting(false);
  };

  const handleUpdate = async (data: Record<string, unknown>) => {
    if (!editing) return;
    setSubmitting(true);
    try {
      await tasksApi.updateTask(editing.id, data as any);
      setEditing(null);
      load();
    } catch { /* ignore */ }
    setSubmitting(false);
  };

  const handleDelete = async () => {
    if (!deleting) return;
    try {
      await tasksApi.deleteTask(deleting.id);
      setDeleting(null);
      load();
    } catch { /* ignore */ }
  };

  const tabLabel = (key: string) => {
    const map: Record<string, string> = {
      all: tc('all'),
      pending: t('pending'),
      today: t('dueToday'),
      overdue: t('overdue'),
      done: t('done'),
    };
    return map[key] || key;
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-text-primary">{t('title')}</h1>
        <button onClick={() => setShowCreate(true)} className="btn-primary text-sm">
          + {t('newTask')}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 border-b border-dark-border">
        {TABS.map((key) => (
          <button
            key={key}
            onClick={() => handleTabChange(key)}
            className={clsx(
              'px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px',
              tab === key
                ? 'text-primary border-primary'
                : 'text-text-muted border-transparent hover:text-text-secondary'
            )}
          >
            {tabLabel(key)}
          </button>
        ))}
      </div>

      {/* List */}
      {loading ? (
        <Skeleton rows={6} />
      ) : tasks.length === 0 ? (
        <EmptyState message={t('noTasks')} />
      ) : (
        <TaskList
          tasks={tasks}
          onToggle={handleToggle}
          onEdit={setEditing}
          onDelete={setDeleting}
        />
      )}

      <Pagination
        page={params.page || 1}
        pageSize={params.page_size || 20}
        total={total}
        onChange={(p) => setParams((prev) => ({ ...prev, page: p }))}
      />

      {/* Create Modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title={t('newTask')} size="md">
        <TaskForm onSubmit={handleCreate} submitting={submitting} />
      </Modal>

      {/* Edit Modal */}
      <Modal open={!!editing} onClose={() => setEditing(null)} title={t('editTask')} size="md">
        {editing && (
          <TaskForm initial={editing} onSubmit={handleUpdate} submitting={submitting} />
        )}
      </Modal>

      {/* Delete Confirm */}
      <Modal open={!!deleting} onClose={() => setDeleting(null)} title={tc('delete')} size="sm">
        <p className="text-text-secondary mb-4">{tc('deleteConfirm')}</p>
        <div className="flex gap-2 justify-end">
          <button onClick={() => setDeleting(null)} className="btn-secondary text-sm">{tc('cancel')}</button>
          <button onClick={handleDelete} className="btn-primary text-sm bg-red-500 hover:bg-red-600">{tc('delete')}</button>
        </div>
      </Modal>
    </div>
  );
}
