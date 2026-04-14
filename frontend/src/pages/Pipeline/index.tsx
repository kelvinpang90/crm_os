import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  DndContext,
  DragEndEvent,
  DragOverEvent,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
} from '@dnd-kit/core';
import { pipelineApi, type PipelineStage } from '@/services/pipeline';
import type { ContactStatus } from '@/types';
import PipelineColumn from './PipelineColumn';
import Skeleton from '@/components/common/Skeleton';

export default function PipelinePage() {
  const { t } = useTranslation('common');
  const navigate = useNavigate();
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

    const contactId = active.id as string;
    const targetStatus = over.id as string;

    // Find which stage the contact currently belongs to
    const sourceStage = stages.find((s) =>
      s.contacts.some((c) => c.id === contactId)
    );
    if (!sourceStage || sourceStage.status === targetStatus) return;

    // Optimistic update
    const contact = sourceStage.contacts.find((c) => c.id === contactId);
    if (!contact) return;

    setStages((prev) =>
      prev.map((s) => {
        if (s.status === sourceStage.status) {
          const filtered = s.contacts.filter((c) => c.id !== contactId);
          return {
            ...s,
            count: filtered.length,
            total_value: s.total_value - contact.deal_value,
            contacts: filtered,
          };
        }
        if (s.status === targetStatus) {
          const updated = { ...contact, status: targetStatus };
          return {
            ...s,
            count: s.count + 1,
            total_value: s.total_value + contact.deal_value,
            contacts: [...s.contacts, updated],
          };
        }
        return s;
      })
    );

    try {
      await pipelineApi.updateContactStatus(contactId, targetStatus as ContactStatus);
    } catch {
      // Rollback on failure
      load();
    }
  };

  const handleCardClick = (contactId: string) => {
    navigate(`/contacts?contact_id=${contactId}`);
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
                onCardClick={handleCardClick}
              />
            ))}
          </div>
        </DndContext>
      )}
    </div>
  );
}
