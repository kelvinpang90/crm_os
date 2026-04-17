import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  DndContext,
  DragEndEvent,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
} from '@dnd-kit/core';
import { pipelineApi, type PipelineStage } from '@/services/pipeline';
import type { DealStatus } from '@/types';
import PipelineColumn from './PipelineColumn';
import Skeleton from '@/components/common/Skeleton';

export default function PipelinePage() {
  const { t } = useTranslation('common');
  const [stages, setStages] = useState<PipelineStage[]>([]);
  const [loading, setLoading] = useState(true);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  );

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await pipelineApi.getPipeline();
      setStages(res.data.data.stages);
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) return;

    const dealId = active.id as string;

    const validStatuses = stages.map((s) => s.status);
    let targetStatus = over.id as string;
    if (!validStatuses.includes(targetStatus)) {
      const targetStage = stages.find((s) =>
        s.deals.some((d) => d.id === targetStatus)
      );
      if (!targetStage) return;
      targetStatus = targetStage.status;
    }

    const sourceStage = stages.find((s) =>
      s.deals.some((d) => d.id === dealId)
    );
    if (!sourceStage || sourceStage.status === targetStatus) return;

    const deal = sourceStage.deals.find((d) => d.id === dealId);
    if (!deal) return;

    // Optimistic update
    setStages((prev) =>
      prev.map((s) => {
        if (s.status === sourceStage.status) {
          const filtered = s.deals.filter((d) => d.id !== dealId);
          return {
            ...s,
            count: filtered.length,
            total_value: s.total_value - deal.amount,
            deals: filtered,
          };
        }
        if (s.status === targetStatus) {
          const updated = { ...deal, status: targetStatus };
          return {
            ...s,
            count: s.count + 1,
            total_value: s.total_value + deal.amount,
            deals: [...s.deals, updated],
          };
        }
        return s;
      })
    );

    try {
      await pipelineApi.updateDealStatus(dealId, targetStatus as DealStatus);
    } catch {
      load();
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-text-primary mb-4">{t('nav.pipeline')}</h1>

      {loading ? (
        <Skeleton rows={6} />
      ) : (
        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragEnd={handleDragEnd}
        >
          <div className="flex gap-3 overflow-x-auto pb-4">
            {stages.map((stage) => (
              <PipelineColumn
                key={stage.status}
                stage={stage}
              />
            ))}
          </div>
        </DndContext>
      )}
    </div>
  );
}
