import { 
  LayoutDashboard, 
  FileSearch, 
  Zap, 
  Bell, 
  Globe, 
  Activity, 
  Settings 
} from 'lucide-react';

export const navigationItems = [
  { id: 'dashboard', icon: LayoutDashboard, path: '/dashboard' },
  { id: 'tenders', icon: FileSearch, path: '/tenders' },
  { id: 'matches', icon: Zap, path: '/matches' },
  { id: 'alerts', icon: Bell, path: '/alerts' },
  { id: 'sources', icon: Globe, path: '/sources' },
  { id: 'activity', icon: Activity, path: '/activity' },
  { id: 'settings', icon: Settings, path: '/settings' },
];
