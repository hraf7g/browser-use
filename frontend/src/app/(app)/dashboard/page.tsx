'use client';
import { useTranslation } from '@/context/language-context';
import DashboardHero from '@/components/dashboard/dashboard-hero';
import DashboardStatsRow from '@/components/dashboard/dashboard-stats-row';
import DashboardPriorityTenders from '@/components/dashboard/dashboard-priority-tenders';
import DashboardLiveActivity from '@/components/dashboard/dashboard-live-activity';
import DashboardSourceHealth from '@/components/dashboard/dashboard-source-health';
import DashboardAlertSummary from '@/components/dashboard/dashboard-alert-summary';
import DashboardProfileSummary from '@/components/dashboard/dashboard-profile-summary';

export default function DashboardPage() {
  const { lang } = useTranslation();

  return (
    <div className="max-w-[1600px] mx-auto p-4 lg:p-8 space-y-8">
      {/* 1. Hero / Overview */}
      <DashboardHero />

      {/* 2. Key Stats */}
      <DashboardStatsRow />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
        {/* Left / Middle: Main Intelligence */}
        <div className="xl:col-span-8 space-y-8">
          <DashboardPriorityTenders />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <DashboardAlertSummary />
            <DashboardSourceHealth />
          </div>
        </div>

        {/* Right: Operational Transparency & Profile */}
        <div className="xl:col-span-4 space-y-8 h-full">
          <DashboardLiveActivity />
          <DashboardProfileSummary />
        </div>
      </div>
    </div>
  );
}
