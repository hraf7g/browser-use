'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, Globe } from 'lucide-react';
import { useTranslation } from '@/context/language-context';

const Navbar = () => {
  const { t, lang, setLang, dir } = useTranslation();
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

    const navLinks = [
    { name: t.navbar.howItWorks, href: '#how-it-works' },
    { name: t.navbar.sources, href: '#sources' },
    { name: t.navbar.pricing, href: '#pricing' },
  ];

  return (
    <nav dir={dir}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? 'bg-white/80 dark:bg-navy-900/80 backdrop-blur-md py-3 border-b border-border shadow-sm'
          : 'bg-transparent py-5'
      }`}
    >
      <div className="container mx-auto px-6 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="group flex items-center gap-3">
          <div className="relative w-11 h-11 bg-gradient-to-br from-primary to-blue-700 rounded-2xl flex items-center justify-center text-white font-black text-xl shadow-lg shadow-primary/20 group-hover:scale-105 group-hover:rotate-3 transition-all duration-300">
            <div className="absolute inset-0 bg-white/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity" />
            TW
          </div>
          <span className="text-2xl font-black tracking-tight hidden md:block bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/70">
            {t.navbar.brand}
          </span>
        </Link>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <Link
              key={link.name}
              href={link.href}
              className="text-sm font-medium hover:text-primary transition-colors"
            >
              {link.name}
            </Link>
          ))}
          
          <div className="h-4 w-px bg-border mx-2" />
          
          <Link href="/login" className="text-sm font-medium hover:text-primary transition-colors">
            {t.navbar.login}
          </Link>

          <button 
            onClick={() => setLang(lang === 'ar' ? 'en' : 'ar')}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-navy-800 transition-colors text-sm font-bold border border-border"
          >
            <Globe size={16} />
            {lang === 'ar' ? 'English' : 'العربية'}
          </button>

          <Link
            href="/signup"
            className="bg-primary hover:bg-primary/90 text-white px-6 py-2.5 rounded-full text-sm font-bold transition-all shadow-lg shadow-primary/20"
          >
            {t.navbar.startFree}
          </Link>
        </div>

        {/* Mobile Toggle */}
        <button
          className="md:hidden p-2"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        >
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, x: 100 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 100 }}
            className="fixed inset-0 top-[73px] bg-white dark:bg-navy-900 z-40 md:hidden px-6 py-8 flex flex-col gap-6"
          >
            {navLinks.map((link) => (
              <Link
                key={link.name}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className="text-lg font-semibold border-b border-border pb-4"
              >
                {link.name}
              </Link>
            ))}
            
            <Link 
              href="/login" 
              onClick={() => setMobileMenuOpen(false)}
              className="text-lg font-semibold border-b border-border pb-4"
            >
              {t.navbar.login}
            </Link>

            <button 
              onClick={() => {
                setLang(lang === 'ar' ? 'en' : 'ar');
                setMobileMenuOpen(false);
              }}
              className="flex items-center justify-between text-lg font-semibold border-b border-border pb-4 w-full"
            >
              <span className="flex items-center gap-2">
                <Globe size={20} />
                {lang === 'ar' ? 'Language' : 'اللغة'}
              </span>
              <span className="text-primary">{lang === 'ar' ? 'English' : 'العربية'}</span>
            </button>

            <Link
              href="/signup"
              onClick={() => setMobileMenuOpen(false)}
              className="bg-primary text-white text-center py-4 rounded-xl font-bold shadow-lg shadow-primary/20 mt-4"
            >
              {t.navbar.startFree}
            </Link>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
};

export default Navbar;
