import HomepageHeroVisual from '@/components/homepage/homepage-hero-visual';
import Button from '@/components/ui/Button';

const proofPoints = [
  { value: '24/7', label: 'source monitoring' },
  { value: 'AR + EN', label: 'normalized analysis' },
  { value: 'Minutes', label: 'from signal to action' },
] as const;

export default function Hero() {
  return (
    <section className="section-shell hero-shell" id="top">
      <div className="section-inner hero-grid">
        <div className="hero-copy">
          <div className="hero-kicker">AI Tender Intelligence</div>
          <h1 className="hero-title">Monitor, match, and act on tenders before everyone else.</h1>
          <p className="hero-description">
            Tender Watch turns fragmented procurement feeds into a live opportunity command center —
            surfacing the right tenders, normalizing bilingual requirements, and routing high-fit
            signals to your team while there is still time to win.
          </p>

          <div className="hero-actions">
            <Button href="#final-cta">Request a walkthrough</Button>
            <Button href="#product" variant="secondary">
              Explore the workflow
            </Button>
          </div>

          <div className="hero-proof-row" aria-label="Proof points">
            {proofPoints.map((point) => (
              <div key={point.label} className="metric-pill">
                <strong>{point.value}</strong>
                <span>{point.label}</span>
              </div>
            ))}
          </div>
        </div>

        <HomepageHeroVisual />
      </div>
    </section>
  );
}
