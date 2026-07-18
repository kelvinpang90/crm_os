// Domain rules for the project tracking module: the 12-step catalog and the
// staleness-based alert derivation.
//
// Step *structure* lives here; step *labels* live in locales/{lang}/projects.json
// under `steps.<key>`, so all translatable copy stays in the locale files.
import dayjs from 'dayjs';
import type { Project, ProjectAlertLevel } from '@/types';

export interface ProjectStep {
  no: number; // 1-12
  key: string; // i18n key suffix: t(`steps.${key}`)
  requires_photo?: boolean; // steps 3 & 10 capture photos (mirrors backend photos_for)
  optional?: boolean; // step 6 (deposit) may be skipped
}

export const PROJECT_STEPS: ProjectStep[] = [
  { no: 1, key: 'enquiry' },
  { no: 2, key: 'inspection_scheduled' },
  { no: 3, key: 'inspection_done', requires_photo: true },
  { no: 4, key: 'quotation_sent' },
  { no: 5, key: 'confirmed' },
  { no: 6, key: 'deposit_received', optional: true },
  { no: 7, key: 'work_scheduled' },
  { no: 8, key: 'in_progress' },
  { no: 9, key: 'quality_check' },
  { no: 10, key: 'completion_photos', requires_photo: true },
  { no: 11, key: 'handover_payment' },
  { no: 12, key: 'warranty_active' },
];

export const TOTAL_STEPS = PROJECT_STEPS.length; // 12

export function getStep(no: number): ProjectStep | undefined {
  return PROJECT_STEPS.find((s) => s.no === no);
}

// Pass the `t` from useTranslation('projects').
export type Translate = (key: string) => string;

export function stepName(no: number, t: Translate): string {
  const step = getStep(no);
  if (!step) return '';
  return t(`steps.${step.key}`);
}

// --- Staleness alert rules ---
// Unified rule (per product decision): flag by "days since last update".
export const ALERT_THRESHOLDS = { watch: 3, urgent: 5 } as const;

export function getStaleDays(lastUpdatedAt: string, now: Date = new Date()): number {
  return dayjs(now).diff(dayjs(lastUpdatedAt), 'day');
}

export function getAlertLevel(project: Project, now: Date = new Date()): ProjectAlertLevel {
  // Warranty active = delivered; a long-lived final state that never alerts.
  if (project.current_step >= TOTAL_STEPS) return 'done';
  const days = getStaleDays(project.last_updated_at, now);
  if (days > ALERT_THRESHOLDS.urgent) return 'urgent';
  if (days > ALERT_THRESHOLDS.watch) return 'watch';
  return 'normal';
}
