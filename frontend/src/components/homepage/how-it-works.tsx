const workflowSteps = [
  {
    step: '01',
    title: 'Ingest live issuer activity',
    body: 'Continuously monitor public and private tender sources, then capture new notices, addenda, deadlines, and scope changes as they appear.',
  },
  {
    step: '02',
    title: 'Structure and normalize the brief',
    body: 'Convert messy notices into a usable operating brief with issuer, package type, category, dates, qualification terms, and decision-ready summaries.',
  },
  {
    step: '03',
    title: 'Score fit against your commercial lens',
    body: 'Rank opportunities by geography, sector, scope, value cues, supplier profile, and delivery relevance instead of forwarding everything to everyone.',
  },
  {
    step: '04',
    title: 'Route the signal to the right owner',
    body: 'Push the highest-confidence opportunity to the team that should act, with timing context and the exact rationale behind the match.',
  },
] as const;

export default function HowItWorks() {
  return (
    <section className="section-shell" id="product">
      <div className="section-inner how-it-works-layout">
        <div className="how-it-works-intro">
          <span className="section-label">How it works</span>
          <h2 className="section-title">A live workflow for procurement intelligence, not another static database.</h2>
          <p className="section-lead">
            Inspired by premium product storytelling, the experience moves in a clear operational rhythm:
            scan, structure, qualify, and act. Each step reduces ambiguity so teams can move from passive
            monitoring to confident pursuit.
          </p>
        </div>

        <div className="workflow-grid">
          {workflowSteps.map((step) => (
            <article key={step.step} className="workflow-card framed-panel">
              <span className="workflow-card__step mono-text">Step {step.step}</span>
              <h3>{step.title}</h3>
              <p>{step.body}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
