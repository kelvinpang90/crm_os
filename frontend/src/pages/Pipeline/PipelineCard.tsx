import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { formatMYR } from '@/utils/currency';
import Badge from '@/components/common/Badge';
import type { PipelineStageDeal } from '@/services/pipeline';

interface Props {
  deal: PipelineStageDeal;
}

export default function PipelineCard({ deal }: Props) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: deal.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className="bg-dark-bg border border-dark-border rounded-lg p-3 cursor-grab active:cursor-grabbing hover:border-primary/30 transition-colors"
    >
      <div className="flex items-center gap-2 mb-1">
        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white text-[10px] font-bold shrink-0">
          {deal.contact_name.charAt(0)}
        </div>
        <span className="text-sm font-medium text-text-primary truncate">{deal.contact_name}</span>
      </div>
      {deal.title && (
        <p className="text-xs text-primary/80 truncate mb-0.5">{deal.title}</p>
      )}
      {deal.contact_company && (
        <p className="text-xs text-text-muted truncate mb-1">{deal.contact_company}</p>
      )}
      <div className="flex items-center justify-between mt-2">
        <Badge value={deal.priority} type="priority" size="sm" />
        <span className="text-xs font-medium text-text-secondary">
          {formatMYR(deal.amount)}
        </span>
      </div>
    </div>
  );
}
