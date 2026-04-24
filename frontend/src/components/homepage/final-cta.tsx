import Button from '@/components/ui/Button';

const ctaPoints = [
  'See the monitoring and qualification flow in action',
  'Review how bilingual tender briefs are structured',
  'Discuss the operating model for your team and market coverage',
] as const;

export default function FinalCTA() {
  return (
    <section className="section-shell" id="final-cta">
      <div className="section-inner">
        <div className="final-cta-panel framed-panel">
          <div className="final-cta-copy">
            <span className="section-label">Ready to see it live</span>
            <h2 className="section-title">Turn tender monitoring into an operational advantage.</h2>
            <p className="section-lead">
              If your team is still discovering opportunities too late, translating notices by hand, or
              routing bids without enough context, Tender Watch is being built to change that rhythm.
            </p>

            <ul className="final-cta-points">
              {ctaPoints.map((point) => (
                <li key={point}>{point}</li>
              ))}
            </ul>
          </div>

          <div className="final-cta-actions">
            <Button href="mailto:hello@tenderwatch.ai">Book a walkthrough</Button>
            <Button href="#top" variant="secondary">
              Back to top
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
