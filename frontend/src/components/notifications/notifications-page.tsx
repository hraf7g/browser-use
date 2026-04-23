'use client';

import { useState } from 'react';
import NotificationsPageHeader from './notifications-page-header';
import NotificationsTabs from './notifications-tabs';
import NotificationCenterPanel from './notification-center-panel';
import NotificationPreferencesPanel from './notification-preferences-panel';
import NotificationDeliveryHistoryPanel from './notification-delivery-history-panel';
import { useMonitoringSetup } from '@/context/monitoring-setup-context';

export default function NotificationsPageShell() {
  const { monitoringActive, openSetup } = useMonitoringSetup();
  const [activeTab, setActiveTab] = useState<'center' | 'preferences' | 'history'>('center');

  return (
    <div className="max-w-5xl mx-auto p-4 lg:p-8 space-y-8 min-h-[calc(100vh-64px)]">
      <NotificationsPageHeader monitoringActive={monitoringActive} onOpenSetup={openSetup} />
      <div className="space-y-6">
        <NotificationsTabs activeTab={activeTab} onChange={setActiveTab} />
        <div className="relative">
          {activeTab === 'center' && (
            <NotificationCenterPanel monitoringActive={monitoringActive} onOpenSetup={openSetup} />
          )}
          {activeTab === 'preferences' && <NotificationPreferencesPanel />}
          {activeTab === 'history' && (
            <NotificationDeliveryHistoryPanel monitoringActive={monitoringActive} onOpenSetup={openSetup} />
          )}
        </div>
      </div>
    </div>
  );
}
