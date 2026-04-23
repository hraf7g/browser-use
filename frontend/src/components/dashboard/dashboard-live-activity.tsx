'use client';

import LiveActivityStream from '@/components/activity/live-activity-stream';
import type { ActivityFeedItem } from '@/lib/activity-api-adapter';

export default function DashboardLiveActivity({
  items,
  monitoringActive,
  onOpenSetup,
}: {
  items: ActivityFeedItem[];
  monitoringActive: boolean;
  onOpenSetup: () => void;
}) {
  return (
    <LiveActivityStream
      items={items}
      monitoringActive={monitoringActive}
      onOpenSetup={onOpenSetup}
      variant="dashboard"
    />
  );
}
