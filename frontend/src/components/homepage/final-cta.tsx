'use client';
import { useTranslation } from '@/context/language-context';
import { motion } from 'framer-motion';
import Link from 'next/link';

export default function FinalCTA() {
  const { t } = useTranslation();

  return (
    <section className="py-24 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-6">
        <div className="relative z-10 bg-blue-600 rounded-[3rem] p-12 md:p-24 text-center text-white shadow-2xl shadow-blue-500/20">
          <motion.h2 
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            className="text-4xl md:text-6xl font-black mb-8 tracking-tighter"
          >
            {t.finalCta.title}
          </motion.h2>
          <p className="text-blue-100 text-xl mb-12 max-w-2xl mx-auto">{t.finalCta.desc}</p>
          <Link href="/signup" className="inline-flex px-10 py-5 bg-white text-blue-600 rounded-full font-black text-xl hover:scale-105 active:scale-95 transition-all shadow-xl">
            {t.finalCta.button}
          </Link>
        </div>
      </div>
      
      {/* Background patterns */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-blue-500/10 via-transparent to-transparent -z-10" />
    </section>
  );
}
