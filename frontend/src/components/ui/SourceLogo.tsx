import React from 'react';
import { Shield, Building2, Globe, FileText, Anchor, Landmark, Briefcase, Network } from 'lucide-react';

type SourceLogoProps = {
  portalKey: string;
  className?: string;
  size?: number;
};

export const SourceLogo: React.FC<SourceLogoProps> = ({ portalKey, className = '', size = 20 }) => {
  const getLogoConfig = () => {
    switch (portalKey.toLowerCase()) {
      case 'saudi etimad':
      case 'اعتماد':
      case 'منصة اعتماد':
        return {
          icon: <Shield size={size} />,
          bg: 'bg-emerald-100 dark:bg-emerald-900/30',
          text: 'text-emerald-600 dark:text-emerald-400',
        };
      case 'dubai esupply':
      case 'التوريد الإلكتروني':
        return {
          icon: <Network size={size} />,
          bg: 'bg-blue-100 dark:bg-blue-900/30',
          text: 'text-blue-600 dark:text-blue-400',
        };
      case 'qatar monaqasat':
      case 'مناقصات':
      case 'مناقصات قطر':
        return {
          icon: <FileText size={size} />,
          bg: 'bg-rose-100 dark:bg-rose-900/30',
          text: 'text-rose-600 dark:text-rose-400',
        };
      case 'oman tender board':
      case 'مجلس المناقصات':
      case 'مجلس المناقصات - عُمان':
        return {
          icon: <Anchor size={size} />,
          bg: 'bg-red-100 dark:bg-red-900/30',
          text: 'text-red-600 dark:text-red-400',
        };
      case 'bahrain tender board':
      case 'مجلس المناقصات - البحرين':
        return {
          icon: <Landmark size={size} />,
          bg: 'bg-red-100 dark:bg-red-900/30',
          text: 'text-red-600 dark:text-red-400',
        };
      case 'federal mof':
      case 'وزارة المالية':
        return {
          icon: <Building2 size={size} />,
          bg: 'bg-indigo-100 dark:bg-indigo-900/30',
          text: 'text-indigo-600 dark:text-indigo-400',
        };
      case 'saudi misa':
      case 'وزارة الاستثمار':
        return {
          icon: <Briefcase size={size} />,
          bg: 'bg-emerald-100 dark:bg-emerald-900/30',
          text: 'text-emerald-600 dark:text-emerald-400',
        };
      default:
        return {
          icon: <Globe size={size} />,
          bg: 'bg-slate-100 dark:bg-slate-800',
          text: 'text-slate-600 dark:text-slate-400',
        };
    }
  };

  const config = getLogoConfig();

  return (
    <div className={`flex items-center justify-center rounded-md p-1.5 ${config.bg} ${config.text} ${className}`}>
      {config.icon}
    </div>
  );
};
