'use client';

import { Save } from 'lucide-react';
import { useTranslation } from '@/context/language-context';

export default function ProfileSaveBar({
  visible,
  dirty,
  saving,
  saveError,
  saveSuccess,
  onSave,
  onReset,
}: {
  visible: boolean;
  dirty: boolean;
  saving: boolean;
  saveError: string | null;
  saveSuccess: string | null;
  onSave: () => void;
  onReset: () => void;
}) {
  const { t } = useTranslation();

  if (!visible) {
    return null;
  }

  const message = saveError
    ? saveError
    : saveSuccess
      ? saveSuccess
      : dirty
        ? t.profilePage.saveBar.dirty
        : t.profilePage.saveBar.saved;

  return (
    <div className="sticky bottom-4 z-30 mt-8">
      <div className="mx-auto flex max-w-5xl flex-col gap-3 rounded-[24px] border border-slate-200 bg-white/95 px-5 py-4 shadow-2xl backdrop-blur dark:border-slate-800 dark:bg-slate-900/95 sm:flex-row sm:items-center sm:justify-between">
        <p className={`text-sm font-medium ${saveError ? 'text-red-700 dark:text-red-300' : saveSuccess ? 'text-emerald-700 dark:text-emerald-300' : 'text-slate-700 dark:text-slate-200'}`}>{message}</p>
        <div className="flex flex-col gap-3 sm:flex-row">
          <button
            type="button"
            onClick={onReset}
            disabled={saving || !dirty}
            className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
          >
            {t.profilePage.actions.reset}
          </button>
          <button
            type="button"
            onClick={onSave}
            disabled={saving || !dirty}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Save size={16} />
            {saving ? t.profilePage.actions.saving : t.profilePage.actions.save}
          </button>
        </div>
      </div>
    </div>
  );
}
