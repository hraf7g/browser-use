const offerCards = [
  {
    title: 'For commercial teams',
    body: 'See the right public and private opportunities sooner, with enough context to decide where to pursue and where to pass.',
  },
  {
    title: 'For bid and proposal teams',
    body: 'Work from a normalized brief instead of re-reading raw notices, translating clauses manually, and reconstructing deadlines from scratch.',
  },
  {
    title: 'For leadership',
    body: 'Gain a clearer view of market activity, pipeline quality, response discipline, and where tender intelligence is creating advantage.',
  },
] as const;

export default function Offers() {
  return (
    <section className="section-shell" id="offers">
      <div className="section-inner offers-layout">
        <div className="offers-copy">
          <span className="section-label">What Tender Watch offers</span>
          <h2 className="section-title">A better tender motion for every team involved in pursuit.</h2>
          <p className="section-lead">
            The product is not just for monitoring. It improves how opportunities are understood,
            prioritized, and acted on across the full decision chain — from first signal to internal
            ownership.
          </p>
        </div>

        <div className="offers-grid">
          {offerCards.map((card) => (
            <article key={card.title} className="offers-card framed-panel">
              <h3>{card.title}</h3>
              <p>{card.body}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
