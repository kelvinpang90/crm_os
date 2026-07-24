import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Modal from '@/components/common/Modal';

const SCORES = Array.from({ length: 10 }, (_, i) => i + 1);
const CANVAS_W = 600;
const CANVAS_H = 180;

interface Props {
  open: boolean;
  customerName: string;
  onClose: () => void;
  onSubmit: (payload: { satisfaction_score: number; customer_feedback: string; signature_data: string }) => Promise<void>;
}

export default function WarrantyConfirmModal({ open, customerName, onClose, onSubmit }: Props) {
  const { t } = useTranslation('projects');
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const drawingRef = useRef(false);

  const [score, setScore] = useState<number | null>(null);
  const [feedback, setFeedback] = useState('');
  const [hasSignature, setHasSignature] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const reset = () => {
    setScore(null);
    setFeedback('');
    setHasSignature(false);
    setError(null);
    setSubmitting(false);
    clearCanvas();
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const getCanvasPoint = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    return { x: (e.clientX - rect.left) * scaleX, y: (e.clientY - rect.top) * scaleY };
  };

  const handlePointerDown = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current!;
    canvas.setPointerCapture(e.pointerId);
    const ctx = canvas.getContext('2d')!;
    const { x, y } = getCanvasPoint(e);
    ctx.beginPath();
    ctx.moveTo(x, y);
    drawingRef.current = true;
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!drawingRef.current) return;
    const canvas = canvasRef.current!;
    const ctx = canvas.getContext('2d')!;
    const { x, y } = getCanvasPoint(e);
    ctx.lineWidth = 2.5;
    ctx.lineCap = 'round';
    ctx.strokeStyle = '#000000';
    ctx.lineTo(x, y);
    ctx.stroke();
    setHasSignature(true);
  };

  const handlePointerUp = () => {
    drawingRef.current = false;
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    canvas.getContext('2d')!.clearRect(0, 0, canvas.width, canvas.height);
    setHasSignature(false);
  };

  const handleSubmit = async () => {
    if (score === null) {
      setError(t('warranty_confirm.validation_score'));
      return;
    }
    if (!hasSignature) {
      setError(t('warranty_confirm.validation_signature'));
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const signature_data = canvasRef.current!.toDataURL('image/png');
      await onSubmit({ satisfaction_score: score, customer_feedback: feedback.trim(), signature_data });
      reset();
    } catch {
      setSubmitting(false);
    }
  };

  return (
    <Modal open={open} onClose={handleClose} title={t('warranty_confirm.title')} size="md">
      <p className="text-xs text-text-muted mb-4">
        {customerName} · {t('warranty_confirm.intro')}
      </p>

      <div className="mb-4">
        <label className="block text-xs text-text-muted mb-1">
          {t('warranty_confirm.score_label')} <span className="text-status-lost">*</span>
        </label>
        <div className="flex flex-wrap gap-1.5">
          {SCORES.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setScore(s)}
              className={`w-8 h-8 text-sm rounded-lg border transition-colors ${
                score === s
                  ? 'bg-primary border-primary text-white'
                  : 'border-dark-border text-text-secondary hover:bg-dark-hover'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-4">
        <label className="block text-xs text-text-muted mb-1">{t('warranty_confirm.feedback_label')}</label>
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder={t('warranty_confirm.feedback_placeholder')}
          rows={3}
          className="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary/60 resize-none"
        />
      </div>

      <div className="mb-2">
        <div className="flex items-center justify-between mb-1">
          <label className="block text-xs text-text-muted">
            {t('warranty_confirm.signature_label')} <span className="text-status-lost">*</span>
          </label>
          <button
            type="button"
            onClick={clearCanvas}
            className="text-xs text-text-muted hover:text-text-primary transition-colors"
          >
            {t('warranty_confirm.clear_signature')}
          </button>
        </div>
        <canvas
          ref={canvasRef}
          width={CANVAS_W}
          height={CANVAS_H}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerUp}
          className="w-full bg-dark-bg border border-dark-border rounded-lg touch-none"
          style={{ height: CANVAS_H, cursor: 'crosshair' }}
        />
        {!hasSignature && (
          <p className="text-[11px] text-text-muted mt-1">{t('warranty_confirm.signature_placeholder')}</p>
        )}
      </div>

      {error && <p className="text-xs text-status-lost mt-2">{error}</p>}

      <div className="flex justify-end gap-2 mt-4">
        <button onClick={handleClose} className="px-4 py-2 text-sm text-text-muted hover:text-text-primary transition-colors">
          {t('actions.cancel')}
        </button>
        <button
          onClick={handleSubmit}
          disabled={submitting}
          className="px-4 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          {submitting ? t('warranty_confirm.submitting') : t('warranty_confirm.submit')}
        </button>
      </div>
    </Modal>
  );
}
