'use client';
import { startTransition, useDeferredValue, useEffect, useMemo, useState } from 'react';
import TendersPageHeader from '@/components/tenders/tenders-page-header';
import TendersSearchBar from '@/components/tenders/tenders-search-bar';
import TendersFilters from '@/components/tenders/tenders-filters';
import TendersActiveFilters from '@/components/tenders/tenders-active-filters';
import TendersResultsToolbar from '@/components/tenders/tenders-results-toolbar';
import TendersList, { type UITenderItem } from '@/components/tenders/tenders-list';
import { tenderApi, type TenderListApiItem } from '@/lib/tender-api-adapter';

function getSourceLabel(sourceUrl: string) {
  try {
    const hostname = new URL(sourceUrl).hostname.replace(/^www\./, '');
    return hostname;
  } catch {
    return 'Official Source';
  }
}

function mapTenderToUi(item: TenderListApiItem): UITenderItem {
  const closingDate = new Date(item.closing_date);
  const diffDays = Math.max(0, Math.ceil((closingDate.getTime() - Date.now()) / 86_400_000));

  return {
    id: item.id,
    title: item.title,
    entity: item.issuing_entity,
    source: getSourceLabel(item.source_url),
    reference: item.tender_ref ?? item.id.slice(0, 8),
    daysLeft: diffDays,
    isNew: diffDays <= 14,
    isMatched: false,
    matchedKeywords: [],
  };
}

export default function TendersDiscoveryPage() {
  const [search, setSearch] = useState('');
  const deferredSearch = useDeferredValue(search);
  const [sort, setSort] = useState<'relevance' | 'newest' | 'closingSoon'>('relevance');
  const [items, setItems] = useState<UITenderItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    tenderApi
      .list({
        page: 1,
        limit: 20,
        search: deferredSearch.trim() || undefined,
      })
      .then((response) => {
        if (cancelled) {
          return;
        }
        const mapped = response.items.map(mapTenderToUi);
        setItems(mapped);
        setTotal(response.total);
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setError(err.message);
          setItems([]);
          setTotal(0);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [deferredSearch]);

  const sortedItems = useMemo(() => {
    const next = [...items];
    if (sort === 'closingSoon') {
      next.sort((a, b) => a.daysLeft - b.daysLeft);
    } else if (sort === 'newest') {
      next.sort((a, b) => Number(b.isNew) - Number(a.isNew));
    }
    return next;
  }, [items, sort]);

  const newCount = useMemo(() => items.filter((item) => item.isNew).length, [items]);
  const closingSoonCount = useMemo(() => items.filter((item) => item.daysLeft <= 7).length, [items]);

  return (
    <div className="max-w-7xl mx-auto p-4 lg:p-8 space-y-8">
      {/* Header Area */}
      <TendersPageHeader total={total} newCount={newCount} closingSoonCount={closingSoonCount} />

      {/* Discovery Surface */}
      <div className="flex flex-col lg:flex-row gap-8 items-start">
        {/* Left: Filters (Desktop Only) */}
        <TendersFilters />

        {/* Right: Search & Results */}
        <div className="flex-1 w-full space-y-6">
          <TendersSearchBar value={search} onChange={(value) => {
            setLoading(true);
            setError(null);
            startTransition(() => setSearch(value));
          }} />
          
          <div className="space-y-4">
            <TendersActiveFilters />
            <TendersResultsToolbar total={total} sort={sort} onSortChange={setSort} />
            <TendersList items={sortedItems} loading={loading} error={error} />
          </div>
        </div>
      </div>
    </div>
  );
}
