'use client';

import { useState } from 'react';
import NotificationsPageHeader from './notifications-page-header';
import NotificationsTabs from './notifications-tabs';
import NotificationCenterPanel from './notification-center-panel';
import NotificationPreferencesPanel from './notification-preferences-panel';
import NotificationDeliveryHistoryPanel from './notification-delivery-history-panel';

export default function NotificationsPageShell() {
  const [activeTab, setActiveTab] = useState<'center' | 'preferences' | 'history'>('center');

  return (
    <div className="max-w-5xl mx-auto p-4 lg:p-8 space-y-8 min-h-[calc(100vh-64px)]">
      <NotificationsPageHeader />
      <div className="space-y-6">
        <NotificationsTabs activeTab={activeTab} onChange={setActiveTab} />
        <div className="relative">
          {activeTab === 'center' && <NotificationCenterPanel />}
          {activeTab === 'preferences' && <NotificationPreferencesPanel />}
          {activeTab === 'history' && <NotificationDeliveryHistoryPanel />}
        </div>
      </div>
    </div>
  );
}
