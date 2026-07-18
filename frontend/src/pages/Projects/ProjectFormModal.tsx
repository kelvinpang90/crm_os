import { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { projectsApi } from '@/services/projects';
import { PROJECT_STEPS, stepName } from './steps';
import type { Project, ProjectInput } from '@/types';

// Sentinel select value that switches the manager field to free-text entry.
const ADD_NEW = '__add_new__';

interface Props {
  project?: Project | null; // present = edit mode
  managers: string[]; // existing manager names, for the picker
  onClose: () => void;
  onSaved: () => void;
}

export default function ProjectFormModal({ project, managers, onClose, onSaved }: Props) {
  const { t } = useTranslation('projects');
  const isEdit = Boolean(project);

  const [form, setForm] = useState<ProjectInput>({
    customer_name: project?.customer_name ?? '',
    address: project?.address ?? '',
    service_type: project?.service_type ?? '',
    project_manager: project?.project_manager ?? '',
    current_step: project?.current_step ?? 1,
  });
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Keep the project's own manager selectable even if it's missing from the list.
  const managerOptions = useMemo(() => {
    const set = new Set(managers.filter(Boolean));
    if (project?.project_manager) set.add(project.project_manager);
    return Array.from(set).sort();
  }, [managers, project]);

  // No existing managers to pick from -> go straight to free-text entry.
  const [addingNew, setAddingNew] = useState(managerOptions.length === 0);

  const set = <K extends keyof ProjectInput>(key: K, value: ProjectInput[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const handleSave = async () => {
    // Trim so stray whitespace can't fork a duplicate manager/customer.
    const payload: ProjectInput = {
      ...form,
      customer_name: form.customer_name.trim(),
      address: form.address.trim(),
      service_type: form.service_type.trim(),
      project_manager: form.project_manager.trim(),
    };
    if (!payload.customer_name) {
      setError(t('validation.customer_required'));
      return;
    }
    setSaving(true);
    try {
      if (isEdit && project) {
        await projectsApi.updateProject(project.id, payload);
      } else {
        await projectsApi.createProject(payload);
      }
      onSaved();
    } catch {
      setSaving(false);
    }
  };

  const inputCls =
    'w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary/60';

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-50" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div className="bg-dark-card border border-dark-border rounded-xl w-full max-w-md pointer-events-auto shadow-xl">
          <div className="flex items-center justify-between p-4 border-b border-dark-border">
            <h2 className="text-base font-semibold text-text-primary">
              {isEdit ? t('edit_project') : t('new_project')}
            </h2>
            <button
              onClick={onClose}
              className="p-1 rounded hover:bg-dark-hover text-text-muted hover:text-text-primary transition-colors"
              aria-label={t('actions.close')}
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          <div className="p-4 space-y-4">
            <div>
              <label className="block text-xs text-text-muted mb-1">
                {t('fields.customer')} <span className="text-status-lost">*</span>
              </label>
              <input
                type="text"
                value={form.customer_name}
                onChange={(e) => set('customer_name', e.target.value)}
                className={inputCls}
                autoFocus
              />
            </div>

            <div>
              <label className="block text-xs text-text-muted mb-1">{t('fields.address')}</label>
              <input type="text" value={form.address} onChange={(e) => set('address', e.target.value)} className={inputCls} />
            </div>

            <div>
              <label className="block text-xs text-text-muted mb-1">{t('fields.service_type')}</label>
              <input type="text" value={form.service_type} onChange={(e) => set('service_type', e.target.value)} className={inputCls} />
            </div>

            {/* Manager: pick an existing name, or switch to free-text to add one */}
            <div>
              <label className="block text-xs text-text-muted mb-1">{t('fields.manager')}</label>
              {addingNew ? (
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={form.project_manager}
                    onChange={(e) => set('project_manager', e.target.value)}
                    className={inputCls}
                    placeholder={t('fields.manager_new_placeholder')}
                  />
                  {managerOptions.length > 0 && (
                    <button
                      type="button"
                      onClick={() => {
                        setAddingNew(false);
                        set('project_manager', '');
                      }}
                      className="shrink-0 px-3 py-2 text-xs text-text-secondary border border-dark-border rounded-lg hover:bg-dark-hover transition-colors"
                    >
                      {t('fields.manager_pick_existing')}
                    </button>
                  )}
                </div>
              ) : (
                <select
                  value={form.project_manager}
                  onChange={(e) => {
                    if (e.target.value === ADD_NEW) {
                      setAddingNew(true);
                      set('project_manager', '');
                    } else {
                      set('project_manager', e.target.value);
                    }
                  }}
                  className={inputCls}
                >
                  <option value="">{t('fields.manager_placeholder')}</option>
                  {managerOptions.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                  <option value={ADD_NEW}>{t('fields.manager_add_new')}</option>
                </select>
              )}
            </div>

            <div>
              <label className="block text-xs text-text-muted mb-1">{t('fields.current_step')}</label>
              <select
                value={form.current_step}
                onChange={(e) => set('current_step', Number(e.target.value))}
                className={inputCls}
              >
                {PROJECT_STEPS.map((s) => (
                  <option key={s.no} value={s.no}>
                    {s.no}. {stepName(s.no, t)}
                  </option>
                ))}
              </select>
            </div>

            {error && <p className="text-xs text-status-lost">{error}</p>}
          </div>

          <div className="flex justify-end gap-2 p-4 border-t border-dark-border">
            <button onClick={onClose} className="px-4 py-2 text-sm text-text-muted hover:text-text-primary transition-colors">
              {t('actions.cancel')}
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {saving ? t('actions.saving') : t('actions.save')}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
