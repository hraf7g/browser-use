'use client';
import { useTranslation } from '@/context/language-context';
import { CheckCircle2 } from 'lucide-react';

export default function AuthBrandPanel() {
  const { t } = useTranslation();
  
  const benefits = [t.auth.brand.benefit1, t.auth.brand.benefit2, t.auth.brand.benefit3];

  return (
    <div className="flex flex-col justify-center p-20 w-full">
      <div className="max-w-md">
        <h2 className="text-4xl font-bold tracking-tight text-slate-900 dark:text-white mb-8 leading-tight">
          {t.auth.brand.title}
        </h2>
        
        <div className="space-y-6">
          {benefits.map((benefit, i) => (
            <div key={i} className="flex gap-4">
              <CheckCircle2 className="text-blue-600 shrink-0" size={24} />
              <p className="text-lg text-slate-600 dark:text-slate-400 font-medium">
                {benefit}
              </p>
            </div>
          ))}
        </div>

        {/* Abstract Product Card UI */}
        <div className="mt-16 relative">
          <div className="absolute -inset-4 bg-blue-500/10 blur-3xl rounded-full" />
          <div className="relative p-6 bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <div className="h-4 w-24 bg-slate-100 dark:bg-slate-700 rounded" />
              <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            </div>
            <div className="space-y-3">
              <div className="h-3 w-full bg-slate-50 dark:bg-slate-900 rounded" />
              <div className="h-3 w-4/5 bg-slate-50 dark:bg-slate-900 rounded" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
