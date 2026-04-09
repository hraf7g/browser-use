'use client';
import { motion } from 'framer-motion';
import { useTranslation } from '@/context/language-context';
import { Bell, Search, Zap, Globe } from 'lucide-react';

export default function Offers() {
  const { t, lang } = useTranslation();

  const features = [
    { 
      icon: Bell, 
      color: 'text-blue-600', 
      bg: 'bg-blue-50 dark:bg-blue-900/10',
      title: lang === 'ar' ? 'تنبيهات فورية' : 'Instant Alerts',
      desc: lang === 'ar' ? 'احصل على تنبيه خلال أجزاء من الثانية' : 'Get notified within milliseconds of a tender posting.',
      span: 'col-span-12 md:col-span-4' 
    },
    { 
      icon: Search, 
      color: 'text-indigo-600', 
      bg: 'bg-indigo-50 dark:bg-indigo-900/10',
      title: lang === 'ar' ? 'بحث ذكي' : 'Strategic Search',
      desc: lang === 'ar' ? 'تحدد أدواتنا الفرص بناءً على أنماط فوزك' : 'Our tools identify opportunities based on your win patterns.',
      span: 'col-span-12 md:col-span-8' 
    },
    { 
      icon: Globe, 
      color: 'text-purple-600', 
      bg: 'bg-purple-50 dark:bg-purple-900/10',
      title: lang === 'ar' ? 'تغطية شاملة' : 'MENA Coverage',
      desc: lang === 'ar' ? 'راقب أكثر من ٥٠ مصدراً رسمياً' : 'Monitor 50+ official sources through one unified interface.',
      span: 'col-span-12 md:col-span-8' 
    },
    { 
      icon: Zap, 
      color: 'text-amber-600', 
      bg: 'bg-amber-50 dark:bg-amber-900/10',
      title: lang === 'ar' ? 'ملخصات ذكية' : 'Smart Briefs',
      desc: lang === 'ar' ? 'قم بتلخيص مستندات المناقصات المعقدة' : 'Summarize complex tender documents and identify key compliance.',
      span: 'col-span-12 md:col-span-4' 
    },
  ];

  return (
    <section id="features" className="py-24 bg-slate-50 dark:bg-slate-950/50">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-12 gap-6">
          {features.map((f, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className={`${f.span} group relative p-8 rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 transition-all hover:shadow-2xl hover:shadow-blue-500/5`}
            >
              <div className={`w-12 h-12 rounded-2xl ${f.bg} flex items-center justify-center mb-6`}>
                <f.icon className={f.color} size={24} />
              </div>
              <h3 className="text-xl font-bold mb-3 text-slate-900 dark:text-white leading-tight">
                {f.title}
              </h3>
              <p className="text-slate-600 dark:text-slate-400 leading-relaxed text-sm md:text-base">
                {f.desc}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
