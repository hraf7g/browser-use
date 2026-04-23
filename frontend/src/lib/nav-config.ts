import { 
  LayoutDashboard, 
  FileSearch, 
  Bell, 
  Activity, 
  Target,
} from 'lucide-react';

export const navigationItems = [
  { id: 'dashboard', icon: LayoutDashboard, path: '/dashboard' },
  { id: 'profile', icon: Target, path: '/profile' },
  { id: 'tenders', icon: FileSearch, path: '/tenders' },
  { id: 'notifications', icon: Bell, path: '/notifications' },
  { id: 'activity', icon: Activity, path: '/activity' },
];
