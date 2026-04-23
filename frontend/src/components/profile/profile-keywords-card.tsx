'use client';

import { Pencil, Plus, X } from 'lucide-react';
import { useTranslation } from '@/context/language-context';
import { KEYWORD_LIMIT } from '@/lib/profile-validation';

export default function ProfileKeywordsCard({
  keywords,
  keywordDraft,
  editingKeyword,
  keywordError,
  onDraftChange,
  onDraftKeyDown,
  onCommitKeyword,
  onStartEditKeyword,
  onRemoveKeyword,
  onCancelEdit,
  inputRef,
}: {
  keywords: string[];
  keywordDraft: string;
  editingKeyword: string | null;
  keywordError: string | null;
  onDraftChange: (nextValue: string) => void;
  onDraftKeyDown: (event: React.KeyboardEvent<HTMLInputElement>) => void;
  onCommitKeyword: () => void;
  onStartEditKeyword: (keyword: string) => void;
  onRemoveKeyword: (keyword: string) => void;
  onCancelEdit: () => void;
  inputRef: React.RefObject<HTMLInputElement | null>;
}) {
  const { t } = useTranslation();

  return (
    <section
      id="profile-keywords"
      className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 lg:p-8"
    >
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-2">
            <h2 className="text-xl font-bold tracking-tight text-slate-950 dark:text-white">
              {t.profilePage.keywords.title}
            </h2>
            <p className="max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-400">
              {t.profilePage.keywords.description}
            </p>
          </div>
          <div className="rounded-full bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600 dark:bg-slate-950/50 dark:text-slate-300">
            {t.profilePage.keywords.count
              .replace('{count}', keywords.length.toString())
              .replace('{limit}', KEYWORD_LIMIT.toString())}
          </div>
        </div>

        <div className="rounded-[24px] border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-700 dark:bg-slate-950/40">
          <div className="flex flex-wrap gap-2">
            {keywords.map((keyword) => (
              <div
                key={keyword}
                className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
              >
                <span>{keyword}</span>
                <button
                  type="button"
                  onClick={() => onStartEditKeyword(keyword)}
                  className="text-slate-400 transition-colors hover:text-blue-600 dark:hover:text-blue-400"
                  aria-label={t.profilePage.keywords.edit}
                >
                  <Pencil size={14} />
                </button>
                <button
                  type="button"
                  onClick={() => onRemoveKeyword(keyword)}
                  className="text-slate-400 transition-colors hover:text-red-600 dark:hover:text-red-400"
                  aria-label={t.profilePage.keywords.remove}
                >
                  <X size={14} />
                </button>
              </div>
            ))}
            <input
              ref={inputRef}
              value={keywordDraft}
              onChange={(event) => onDraftChange(event.target.value)}
              onKeyDown={onDraftKeyDown}
              className="min-w-[220px] flex-1 bg-transparent px-2 py-2 text-sm text-slate-700 outline-none placeholder:text-slate-400 dark:text-slate-200"
              placeholder={t.profilePage.keywords.placeholder}
            />
          </div>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <button
            type="button"
            onClick={onCommitKeyword}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-slate-800 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100"
          >
            <Plus size={16} />
            {editingKeyword ? t.profilePage.keywords.update : t.profilePage.keywords.add}
          </button>
          {editingKeyword ? (
            <button
              type="button"
              onClick={onCancelEdit}
              className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
            >
              {t.profilePage.keywords.cancelEdit}
            </button>
          ) : null}
        </div>

        <div className="space-y-2">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {editingKeyword
              ? t.profilePage.keywords.editing.replace('{keyword}', editingKeyword)
              : t.profilePage.keywords.helper}
          </p>
          {keywordError ? (
            <p className="text-sm font-medium text-red-600 dark:text-red-400">{keywordError}</p>
          ) : null}
        </div>
      </div>
    </section>
  );
}
