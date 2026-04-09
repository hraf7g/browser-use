'use client';
import { useTranslation } from '@/context/language-context';
import { motion } from 'framer-motion';
import { Shield, Building2 } from 'lucide-react';

export default function SmeEnterprise() {
  const { t } = useTranslation();

  return (
    <section className="py-24">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid md:grid-cols-2 gap-8">
          <motion.div
            whileHover={{ scale: 1.02 }}
            className="p-10 rounded-3xl bg-blue-600 text-white"
          >
            <Building2 size={40} className="mb-6 opacity-80" />
            <h3 className="text-3xl font-bold mb-4">{t.smeEnterprise.sme.title}</h3>
            <p className="text-blue-100 text-lg leading-relaxed">{t.smeEnterprise.sme.desc}</p>
          </motion.div>

          <motion.div
            whileHover={{ scale: 1.02 }}
            className="p-10 rounded-3xl bg-slate-900 text-white"
          >
            <Shield size={40} className="mb-6 opacity-80" />
            <h3 className="text-3xl font-bold mb-4">{t.smeEnterprise.enterprise.title}</h3>
            <p className="text-slate-400 text-lg leading-relaxed">{t.smeEnterprise.enterprise.desc}</p>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
