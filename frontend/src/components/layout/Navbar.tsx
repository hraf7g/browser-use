'use client';

import { useEffect, useState } from 'react';
import ThemeToggle from '@/components/ui/theme-toggle';

const navigationItems = [
  { href: '#how-it-works', label: 'كيف يعمل' },
  { href: '#sources', label: 'المصادر' },
  { href: '#pricing', label: 'التسعير' },
  { href: '/login', label: 'تسجيل الدخول' },
] as const;

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };

    handleScroll();
    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  useEffect(() => {
    document.body.classList.toggle('homepage-nav-open', isOpen);

    return () => {
      document.body.classList.remove('homepage-nav-open');
    };
  }, [isOpen]);

  const closeMenu = () => setIsOpen(false);

  return (
    <header className={`site-navbar${isScrolled ? ' is-scrolled' : ''}`}>
      <div className="site-navbar__inner">
        <a className="site-brand" href="#top" aria-label="العودة إلى أعلى الصفحة">
          <span className="site-brand__mark" aria-hidden="true">
            <span className="site-brand__mark-inner">TW</span>
          </span>
          <span className="site-brand__copy">
            <strong>تيندر ووتش</strong>
            <span>منصة مراقبة المناقصات بالذكاء الاصطناعي</span>
          </span>
        </a>

        <nav className="site-nav" aria-label="التنقل الرئيسي">
          {navigationItems.map((item) => (
            <a key={item.href} href={item.href} className="site-nav__link">
              {item.label}
            </a>
          ))}
        </nav>

        <div className="site-navbar__actions">
          <ThemeToggle />

          <a className="site-navbar__cta" href="/signup">
            ابدأ مجاناً
          </a>

          <button
            type="button"
            className={`site-navbar__menu-toggle${isOpen ? ' is-open' : ''}`}
            aria-expanded={isOpen}
            aria-controls="mobile-navigation-panel"
            aria-label={isOpen ? 'إغلاق القائمة' : 'فتح القائمة'}
            onClick={() => setIsOpen((current) => !current)}
          >
            <span />
            <span />
            <span />
          </button>
        </div>
      </div>

      <div className={`mobile-nav${isOpen ? ' is-open' : ''}`} aria-hidden={!isOpen}>
        <button className="mobile-nav__backdrop" type="button" aria-label="إغلاق القائمة" onClick={closeMenu} />
        <aside className="mobile-nav__panel" id="mobile-navigation-panel" aria-label="القائمة الجانبية">
          <div className="mobile-nav__header">
            <div className="mobile-nav__brand">
              <span className="site-brand__mark" aria-hidden="true">
                <span className="site-brand__mark-inner">TW</span>
              </span>
              <div className="site-brand__copy">
                <strong>تيندر ووتش</strong>
                <span>مراقبة مستمرة للمصادر الحكومية</span>
              </div>
            </div>

            <button type="button" className="mobile-nav__close" aria-label="إغلاق القائمة" onClick={closeMenu}>
              <span />
              <span />
            </button>
          </div>

          <div className="mobile-nav__links">
            {navigationItems.map((item) => (
              <a key={item.href} href={item.href} className="mobile-nav__link" onClick={closeMenu}>
                <span>{item.label}</span>
                <span className="mobile-nav__arrow" aria-hidden="true">
                  →
                </span>
              </a>
            ))}
          </div>

          <div className="mobile-nav__footer">
            <a className="site-navbar__cta mobile-nav__cta" href="/signup" onClick={closeMenu}>
              ابدأ مجاناً
            </a>
          </div>
        </aside>
      </div>
    </header>
  );
}
