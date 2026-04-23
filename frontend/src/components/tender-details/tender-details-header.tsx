'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useTranslation } from '@/context/language-context';
import { ArrowLeft, ExternalLink, Bookmark, Share2 } from 'lucide-react';

export default function TenderDetailsHeader({
  title,
  officialUrl,
}: {
  title: string;
  officialUrl: string;
}) {
  const { t, lang } = useTranslation();
  const [savedTenderUrls, setSavedTenderUrls] = useState<string[]>(() => {
    if (typeof window === 'undefined') {
      return [];
    }

    return JSON.parse(window.localStorage.getItem('saved_tender_urls') ?? '[]') as string[];
  });
  const [shareFeedback, setShareFeedback] = useState<string | null>(null);
  const saved = savedTenderUrls.includes(officialUrl);

  function handleToggleSave() {
    if (typeof window === 'undefined') {
      return;
    }

    const nextSavedTenderUrls = new Set(savedTenderUrls);

    if (nextSavedTenderUrls.has(officialUrl)) {
      nextSavedTenderUrls.delete(officialUrl);
    } else {
      nextSavedTenderUrls.add(officialUrl);
    }

    const nextSavedTenderUrlList = Array.from(nextSavedTenderUrls);
    setSavedTenderUrls(nextSavedTenderUrlList);

    window.localStorage.setItem(
      'saved_tender_urls',
      JSON.stringify(nextSavedTenderUrlList)
    );
  }

  async function handleShare() {
    try {
      if (navigator.share) {
        await navigator.share({ title, url: officialUrl });
      } else {
        await navigator.clipboard.writeText(officialUrl);
      }
      setShareFeedback('shared');
      window.setTimeout(() => setShareFeedback(null), 2000);
    } catch {
      setShareFeedback(null);
    }
  }

  return (
    <div className="flex flex-col gap-5 rounded-[28px] border border-slate-200 bg-white px-6 py-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 lg:px-8">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-3">
          <Link
            href="/tenders"
            className="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 transition-colors hover:text-blue-600 dark:text-slate-400 dark:hover:text-blue-400"
          >
            <ArrowLeft size={16} className={lang === 'ar' ? 'rotate-180' : ''} />
            {t.details.back}
          </Link>
          <h1 className="max-w-4xl text-3xl font-bold tracking-tight text-slate-950 dark:text-white lg:text-4xl">
            {title}
          </h1>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <a
            href={officialUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-slate-800 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100"
          >
            <ExternalLink size={16} />
            {t.details.actions.official}
          </a>
          <button
            type="button"
            onClick={handleToggleSave}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-5 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
          >
            <Bookmark size={16} />
            {saved ? `${t.details.actions.save} ✓` : t.details.actions.save}
          </button>
          <button
            type="button"
            onClick={() => void handleShare()}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-5 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700"
          >
            <Share2 size={16} />
            {shareFeedback ? `${t.details.actions.share} ✓` : t.details.actions.share}
          </button>
        </div>
      </div>
    </div>
  );
}
