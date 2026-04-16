import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '@/store/authStore';

export default function RegisterPage() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { register, isLoading, error, clearError } = useAuthStore();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [localErrors, setLocalErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const errors: Record<string, string> = {};
    if (!name.trim() || name.trim().length < 2) {
      errors.name = t('register.nameMin');
    }
    if (!email) {
      errors.email = t('enterEmail');
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = t('invalidEmail');
    }
    if (!password) {
      errors.password = t('enterPassword');
    } else if (password.length < 8) {
      errors.password = t('register.passwordMin');
    } else if (!/[A-Za-z]/.test(password)) {
      errors.password = t('register.passwordLetter');
    } else if (!/\d/.test(password)) {
      errors.password = t('register.passwordDigit');
    }
    if (!confirmPassword) {
      errors.confirmPassword = t('register.confirmRequired');
    } else if (password !== confirmPassword) {
      errors.confirmPassword = t('register.passwordMismatch');
    }
    setLocalErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const clearField = (field: string) => {
    setLocalErrors((p) => {
      const next = { ...p };
      delete next[field];
      return next;
    });
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    clearError();
    if (!validate()) return;

    try {
      await register({ name: name.trim(), email, password, confirm_password: confirmPassword });
      navigate('/dashboard', { replace: true });
    } catch {
      // error is set in store
    }
  };

  return (
    <div className="min-h-screen bg-dark-bg flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            CRM Pro
          </h1>
          <p className="mt-2 text-text-secondary">{t('register.subtitle')}</p>
        </div>

        {/* Register Card */}
        <div className="card p-8">
          <h2 className="text-xl font-semibold text-text-primary mb-6">{t('register.title')}</h2>

          {/* Server error */}
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1.5">
                {t('name')}
              </label>
              <input
                type="text"
                className={`input ${localErrors.name ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
                placeholder={t('register.namePlaceholder')}
                value={name}
                onChange={(e) => { setName(e.target.value); clearField('name'); }}
                autoComplete="name"
              />
              {localErrors.name && <p className="mt-1 text-sm text-red-400">{localErrors.name}</p>}
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1.5">
                {t('email')}
              </label>
              <input
                type="email"
                className={`input ${localErrors.email ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
                placeholder={t('emailPlaceholder')}
                value={email}
                onChange={(e) => { setEmail(e.target.value); clearField('email'); }}
                autoComplete="email"
              />
              {localErrors.email && <p className="mt-1 text-sm text-red-400">{localErrors.email}</p>}
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1.5">
                {t('password')}
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  className={`input pr-10 ${localErrors.password ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
                  placeholder={t('register.passwordPlaceholder')}
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); clearField('password'); }}
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary transition-colors"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
                      <line x1="1" y1="1" x2="23" y2="23" />
                    </svg>
                  ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              </div>
              {localErrors.password && <p className="mt-1 text-sm text-red-400">{localErrors.password}</p>}
              <p className="mt-1 text-xs text-text-muted">{t('register.passwordHint')}</p>
            </div>

            {/* Confirm Password */}
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1.5">
                {t('register.confirmPassword')}
              </label>
              <input
                type={showPassword ? 'text' : 'password'}
                className={`input ${localErrors.confirmPassword ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}`}
                placeholder={t('register.confirmPlaceholder')}
                value={confirmPassword}
                onChange={(e) => { setConfirmPassword(e.target.value); clearField('confirmPassword'); }}
                autoComplete="new-password"
              />
              {localErrors.confirmPassword && <p className="mt-1 text-sm text-red-400">{localErrors.confirmPassword}</p>}
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full h-11 flex items-center justify-center mt-2"
            >
              {isLoading ? (
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              ) : (
                t('register.submit')
              )}
            </button>
          </form>

          {/* Login link */}
          <p className="mt-6 text-center text-sm text-text-secondary">
            {t('register.hasAccount')}{' '}
            <Link to="/login" className="text-primary hover:text-primary/80 font-medium">
              {t('register.goLogin')}
            </Link>
          </p>
        </div>

        <p className="text-center text-text-muted text-xs mt-6">
          CRM Pro v1.0 &copy; 2026
        </p>
      </div>
    </div>
  );
}
