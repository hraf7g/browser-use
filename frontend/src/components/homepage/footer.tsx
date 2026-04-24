const footerLinks = [
  { href: '#product', label: 'Product' },
  { href: '#activity', label: 'Activity' },
  { href: '#trust', label: 'Trust' },
  { href: '#faq', label: 'FAQ' },
] as const;

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="site-footer__inner">
        <div className="site-footer__brand">
          <strong>Tender Watch</strong>
          <span>AI Tender Intelligence for bilingual procurement workflows.</span>
        </div>

        <nav className="site-footer__nav" aria-label="Footer navigation">
          {footerLinks.map((link) => (
            <a key={link.href} href={link.href}>
              {link.label}
            </a>
          ))}
        </nav>

        <div className="site-footer__meta mono-text">Built for signal clarity, timing, and action.</div>
      </div>
    </footer>
  );
}
