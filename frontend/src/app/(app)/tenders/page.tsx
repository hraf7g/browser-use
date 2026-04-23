'use client';
import { startTransition, useDeferredValue, useEffect, useMemo, useState } from 'react';
import TendersPageHeader from '@/components/tenders/tenders-page-header';
import TendersSearchBar from '@/components/tenders/tenders-search-bar';
import TendersFilters from '@/components/tenders/tenders-filters';
import TendersActiveFilters, { type ActiveTenderFilter } from '@/components/tenders/tenders-active-filters';
import TendersResultsToolbar from '@/components/tenders/tenders-results-toolbar';
import TendersList, { type UITenderItem } from '@/components/tenders/tenders-list';
import { useMonitoringSetup } from '@/context/monitoring-setup-context';
import {
  tenderApi,
  type TenderListApiItem,
  type TenderSourceFilterOption,
} from '@/lib/tender-api-adapter';
import { useTranslation } from '@/context/language-context';

function mapTenderToUi(item: TenderListApiItem): UITenderItem {
  const diffDays =
    item.closing_date === null
      ? null
      : Math.max(0, Math.ceil((new Date(item.closing_date).getTime() - Date.now()) / 86_400_000));
  const createdAt = new Date(item.created_at);
  const newDiffDays = Math.ceil((Date.now() - createdAt.getTime()) / 86_400_000);

  return {
    id: item.id,
    title: item.title,
    entity: item.issuing_entity,
    source: item.source_name,
    sourceName: item.source_name,
    reference: item.tender_ref ?? item.id.slice(0, 8),
    daysLeft: diffDays,
    isNew: newDiffDays <= 14,
    isMatched: item.is_matched,
    matchedKeywords: item.matched_keywords,
    matchedCountryCodes: item.matched_country_codes,
    matchedIndustryCodes: item.matched_industry_codes,
  };
}

type TenderFiltersState = {
  matchOnly: boolean;
  newOnly: boolean;
  closingSoon: boolean;
  sourceIds: string[];
};

export default function TendersDiscoveryPage() {
  const { t } = useTranslation();
  const { monitoringActive, openSetup } = useMonitoringSetup();
  const [search, setSearch] = useState('');
  const deferredSearch = useDeferredValue(search);
  const [sort, setSort] = useState<'relevance' | 'newest' | 'closingSoon'>('relevance');
  const [items, setItems] = useState<UITenderItem[]>([]);
  const [availableSources, setAvailableSources] = useState<TenderSourceFilterOption[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<TenderFiltersState>({
    matchOnly: false,
    newOnly: false,
    closingSoon: false,
    sourceIds: [],
  });

  useEffect(() => {
    let cancelled = false;

    tenderApi
      .list({
        page: 1,
        limit: 20,
        search: deferredSearch.trim() || undefined,
        source_ids: filters.sourceIds.length > 0 ? filters.sourceIds.join(',') : undefined,
        match_only: filters.matchOnly || undefined,
        new_only: filters.newOnly || undefined,
        closing_soon: filters.closingSoon || undefined,
        sort,
      })
      .then((response) => {
        if (cancelled) {
          return;
        }
        const mapped = response.items.map(mapTenderToUi);
        setItems(mapped);
        setAvailableSources(response.available_sources ?? []);
        setTotal(response.total);
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setError(err.message);
          setItems([]);
          setAvailableSources([]);
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
  }, [deferredSearch, filters, sort]);

  const newCount = useMemo(() => items.filter((item) => item.isNew).length, [items]);
  const closingSoonCount = useMemo(
    () =>
      items.filter((item) => item.daysLeft !== null && item.daysLeft > 0 && item.daysLeft <= 7).length,
    [items]
  );
  const activeFilters = useMemo<ActiveTenderFilter[]>(() => {
    const next: ActiveTenderFilter[] = [];
    if (filters.matchOnly) {
      next.push({ id: 'matchOnly', label: t.tenders.filters.matchOnly });
    }
    if (filters.newOnly) {
      next.push({ id: 'newOnly', label: t.tenders.filters.newOnly });
    }
    if (filters.closingSoon) {
      next.push({ id: 'closingSoon', label: t.tenders.sort.closingSoon });
    }
    for (const sourceId of filters.sourceIds) {
      const source = availableSources.find((item) => item.id === sourceId);
      if (source) {
        next.push({ id: `source:${sourceId}`, label: source.name });
      }
    }
    return next;
  }, [availableSources, filters.closingSoon, filters.matchOnly, filters.newOnly, filters.sourceIds, t.tenders.filters.matchOnly, t.tenders.filters.newOnly, t.tenders.sort.closingSoon]);

  function resetFilters() {
    setLoading(true);
    setError(null);
    setFilters({
      matchOnly: false,
      newOnly: false,
      closingSoon: false,
      sourceIds: [],
    });
  }

  function removeActiveFilter(filterId: string) {
    if (filterId === 'matchOnly') {
      setLoading(true);
      setError(null);
      setFilters((current) => ({ ...current, matchOnly: false }));
      return;
    }
    if (filterId === 'newOnly') {
      setLoading(true);
      setError(null);
      setFilters((current) => ({ ...current, newOnly: false }));
      return;
    }
    if (filterId === 'closingSoon') {
      setLoading(true);
      setError(null);
      setFilters((current) => ({ ...current, closingSoon: false }));
      return;
    }
    if (filterId.startsWith('source:')) {
      const sourceId = filterId.replace('source:', '');
      setLoading(true);
      setError(null);
      setFilters((current) => ({
        ...current,
        sourceIds: current.sourceIds.filter((item) => item !== sourceId),
      }));
    }
  }

  return (
    <div className="max-w-7xl mx-auto p-4 lg:p-8 space-y-8">
      {/* Header Area */}
      <TendersPageHeader
        total={total}
        newCount={newCount}
        closingSoonCount={closingSoonCount}
        monitoringActive={monitoringActive}
        onOpenSetup={openSetup}
      />

      {/* Discovery Surface */}
      <div className="flex flex-col lg:flex-row gap-8 items-start">
        {/* Left: Filters (Desktop Only) */}
        <TendersFilters
          filters={filters}
          availableSources={availableSources}
          onToggleMatchOnly={() => {
            setLoading(true);
            setError(null);
            setFilters((current) => ({ ...current, matchOnly: !current.matchOnly }));
          }}
          onToggleNewOnly={() => {
            setLoading(true);
            setError(null);
            setFilters((current) => ({ ...current, newOnly: !current.newOnly }));
          }}
          onToggleClosingSoon={() => {
            setLoading(true);
            setError(null);
            setFilters((current) => ({ ...current, closingSoon: !current.closingSoon }));
          }}
          onToggleSource={(sourceId) =>
            {
              setLoading(true);
              setError(null);
              setFilters((current) => ({
                ...current,
                sourceIds: current.sourceIds.includes(sourceId)
                  ? current.sourceIds.filter((item) => item !== sourceId)
                  : [...current.sourceIds, sourceId],
              }));
            }
          }
          onReset={resetFilters}
        />

        {/* Right: Search & Results */}
        <div className="flex-1 w-full space-y-6">
          <TendersSearchBar value={search} onChange={(value) => {
            setLoading(true);
            setError(null);
            startTransition(() => setSearch(value));
          }} />
          
          <div className="space-y-4">
            <TendersActiveFilters filters={activeFilters} onRemove={removeActiveFilter} onReset={resetFilters} />
            <TendersResultsToolbar
              total={total}
              sort={sort}
              onSortChange={(nextSort) => {
                setLoading(true);
                setError(null);
                setSort(nextSort);
              }}
            />
            <TendersList
              items={items}
              loading={loading}
              error={error}
              monitoringActive={monitoringActive}
              onOpenSetup={openSetup}
              searchTerm={deferredSearch}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
