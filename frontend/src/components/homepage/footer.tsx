'use client';

import Link from 'next/link';

import { useTranslation } from '@/context/language-context';
import { Search } from 'lucide-react';

export default function Footer() {
  const { t } = useTranslation();
  const links = [
    { label: t.nav.features, href: '#features' },
    { label: t.nav.howItWorks, href: '#how' },
    { label: t.nav.solutions, href: '#solutions' },
    { label: t.homepageActivity.badge, href: '#activity' },
    { label: t.nav.signIn, href: '/login' },
    { label: t.nav.getStarted, href: '/signup' },
  ];

  return (
    <footer className="py-20 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex flex-col md:flex-row justify-between items-center gap-8 mb-12">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/20">
              <Search className="text-white" size={20} />
            </div>
            <span className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
              Tender<span className="text-blue-600">Watch</span>
            </span>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-6 text-sm font-medium text-slate-600 dark:text-slate-400">
            {links.map((link) => (
              <Link key={link.href} href={link.href} className="hover:text-blue-600 transition-colors">
                {link.label}
              </Link>
            ))}
          </div>
        </div>
        
        <div className="text-center text-slate-400 text-sm">
          {t.footer.copyright}
        </div>
      </div>
    </footer>
  );
}
