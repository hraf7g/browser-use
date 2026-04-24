import Button from '@/components/ui/Button';

const navigationItems = [
  { href: '#product', label: 'Product' },
  { href: '#workflow', label: 'Workflow' },
  { href: '#activity', label: 'Activity' },
  { href: '#faq', label: 'FAQ' },
] as const;

export default function Header() {
  return (
    <header className="site-header">
      <div className="site-header__inner">
        <a className="site-brand" href="#top" aria-label="Tender Watch home">
          <span className="site-brand__mark" />
          <div className="site-brand__copy">
            <strong>Tender Watch</strong>
            <span>AI Tender Intelligence</span>
          </div>
        </a>

        <nav className="site-nav" aria-label="Primary navigation">
          {navigationItems.map((item) => (
            <a key={item.href} className="site-nav__link" href={item.href}>
              {item.label}
            </a>
          ))}
        </nav>

        <div className="site-header__actions">
          <Button href="#final-cta" variant="secondary">
            Book Demo
          </Button>
        </div>
      </div>
    </header>
  );
}
