import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { useTranslation } from 'react-i18next';
import PipelineCard from './PipelineCard';
import type { PipelineStage } from '@/services/pipeline';

interface Props {
  stage: PipelineStage;
  onCardClick?: (contactId: string) => void;
}

const STATUS_COLORS: Record<string, string> = {
  lead: 'border-t-blue-500',
  following: 'border-t-cyan-500',
  negotiating: 'border-t-orange-500',
  won: 'border-t-green-500',
  lost: 'border-t-red-500',
};

export default function PipelineColumn({ stage, onCardClick }: Props) {
  const { t } = useTranslation('common');
  const { setNodeRef, isOver } = useDroppable({ id: stage.status });
  const colorClass = STATUS_COLORS[stage.status] || 'border-t-gray-500';
  const ids = stage.contacts.map((c) => c.id);

  return (
    <div
      ref={setNodeRef}
      className={`flex flex-col min-w-[260px] w-full bg-dark-card rounded-lg border border-dark-border border-t-2 ${colorClass} ${
        isOver ? 'ring-1 ring-primary/40' : ''
      }`}
    >
      {/* Header */}
      <div className="p-3 border-b border-dark-border">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-text-primary">
            {t(`statusLabels.${stage.status}`, stage.status)}
          </h4>
          <span className="text-xs text-text-muted bg-dark-hover px-2 py-0.5 rounded-full">
            {stage.count}
          </span>
        </div>
        <p className="text-xs text-text-muted mt-1">
          ¥{stage.total_value >= 10000
            ? `${(stage.total_value / 10000).toFixed(1)}万`
            : stage.total_value.toLocaleString()}
        </p>
      </div>

      {/* Cards */}
      <div className="flex-1 p-2 space-y-2 overflow-y-auto max-h-[calc(100vh-260px)]">
        <SortableContext items={ids} strategy={verticalListSortingStrategy}>
          {stage.contacts.map((c) => (
            <PipelineCard
              key={c.id}
              contact={c}
              onClick={() => onCardClick?.(c.id)}
            />
          ))}
        </SortableContext>
        {stage.contacts.length === 0 && (
          <p className="text-xs text-text-muted text-center py-4">--</p>
        )}
      </div>
    </div>
  );
}
