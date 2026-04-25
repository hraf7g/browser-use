'use client';
import React from 'react';
import { useTranslation } from '@/context/language-context';
import Link from 'next/link';

const Footer = () => {
  const { t, dir } = useTranslation();
  return (
    <footer dir={dir} className="py-20 bg-white dark:bg-navy-950 border-t border-border">
      <div className="container mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 mb-16">
          <div className="col-span-1 lg:col-span-1">
            <div className="flex items-center gap-2 mb-6">
              <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center text-white font-bold text-xl">TW</div>
              <span className="text-xl font-bold tracking-tight">{t.footer.brand}</span>
            </div>
            <p className="text-muted text-sm leading-relaxed mb-6">
              {t.footer.description}
            </p>
          </div>

          <div>
            <h4 className="font-bold mb-6 text-sm">{t.footer.quickLinksTitle}</h4>
            <ul className="space-y-4 text-sm text-muted">
              {t.footer.regions.map((region: string) => (
                <li key={region}>{region}</li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="font-bold mb-6 text-sm">{t.footer.contactTitle}</h4>
            <ul className="space-y-4 text-sm text-muted">
              <li>info@tenderwatch.ai</li>
              <li>+971 4 000 0000</li>
              <li>{t.footer.contact.address}</li>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-border flex flex-col md:flex-row justify-between items-center gap-6">
          <p className="text-xs text-muted">© ٢٠٢٤ {t.footer.brand}. جميع الحقوق محفوظة.</p>
          <div className="flex gap-8 text-xs text-muted">
            <Link href="/privacy" className="hover:text-primary">{t.footer.privacy}</Link>
            <Link href="/terms" className="hover:text-primary">{t.footer.terms}</Link>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
