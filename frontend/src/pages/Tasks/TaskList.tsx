import { useTranslation } from 'react-i18next';
import Badge from '@/components/common/Badge';
import dayjs from 'dayjs';
import type { Task } from '@/types';

interface Props {
  tasks: Task[];
  onToggle: (id: string) => void;
  onEdit: (task: Task) => void;
  onDelete: (task: Task) => void;
}

export default function TaskList({ tasks, onToggle, onEdit, onDelete }: Props) {
  const { t } = useTranslation('tasks');
  const { t: tc } = useTranslation('common');
  const today = dayjs().format('YYYY-MM-DD');

  return (
    <div className="space-y-1">
      {tasks.map((task) => {
        const overdue = !task.is_done && task.due_date && task.due_date < today;
        return (
          <div
            key={task.id}
            className={`flex items-center gap-3 p-3 rounded-lg border transition-colors ${
              task.is_done
                ? 'border-dark-border/30 bg-dark-hover/30'
                : overdue
                ? 'border-red-500/30 bg-red-500/5'
                : 'border-dark-border hover:bg-dark-hover'
            }`}
          >
            {/* Checkbox */}
            <button
              onClick={() => onToggle(task.id)}
              className={`w-5 h-5 rounded-full border-2 shrink-0 flex items-center justify-center transition-colors ${
                task.is_done
                  ? 'bg-green-500 border-green-500 text-white'
                  : 'border-dark-border hover:border-primary'
              }`}
            >
              {task.is_done && (
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              )}
            </button>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className={`text-sm font-medium truncate ${
                  task.is_done ? 'text-text-muted line-through' : 'text-text-primary'
                }`}>
                  {task.title}
                </span>
                <Badge value={task.priority} type="priority" size="sm" />
              </div>
              <div className="flex items-center gap-3 mt-0.5 text-xs text-text-muted">
                {task.contact_name && <span>{task.contact_name}</span>}
                {task.assigned_to_name && <span>→ {task.assigned_to_name}</span>}
                {task.due_date && (
                  <span className={overdue ? 'text-red-400' : ''}>
                    {dayjs(task.due_date).format('MM/DD')}
                  </span>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-1 shrink-0">
              <button
                onClick={() => onEdit(task)}
                className="text-text-muted hover:text-text-primary text-xs px-2 py-1"
              >
                {tc('edit')}
              </button>
              <button
                onClick={() => onDelete(task)}
                className="text-text-muted hover:text-red-400 text-xs px-2 py-1"
              >
                {tc('delete')}
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
