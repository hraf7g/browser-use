const problemSignals = [
  {
    title: 'Fragmented source coverage',
    body: 'Teams still depend on manual portal checks, inbox chains, and remembered bookmarks across ministries, municipalities, and private issuers.',
  },
  {
    title: 'Late qualification decisions',
    body: 'By the time someone reads the documents, translates the scope, and identifies the owner, the response window is already shrinking.',
  },
  {
    title: 'Low-confidence routing',
    body: 'Commercial, bid, and operations teams receive noisy opportunities without fit context, deadline risk, or a common summary to act on.',
  },
] as const;

const problemMetrics = [
  { value: '40+', label: 'tender sources tracked in one operating layer' },
  { value: 'AR ↔ EN', label: 'requirements normalized into a single brief' },
  { value: '< 5 min', label: 'from signal capture to routed opportunity' },
] as const;

export default function Problem() {
  return (
    <section className="section-shell" id="workflow">
      <div className="section-inner problem-layout">
        <div className="problem-copy">
          <span className="section-label">Why procurement teams miss the right bids</span>
          <h2 className="section-title">Most tender workflows break before the team even decides to pursue.</h2>
          <p className="section-lead">
            The issue is rarely access to information. It is the delay between discovery, qualification,
            translation, and ownership. Tender Watch compresses that entire gap into a live operating
            layer, so teams see what matters early enough to respond with intent.
          </p>

          <div className="problem-metrics" aria-label="Tender Watch outcome metrics">
            {problemMetrics.map((metric) => (
              <div key={metric.label} className="problem-metric framed-panel">
                <strong>{metric.value}</strong>
                <span>{metric.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="problem-stack">
          {problemSignals.map((signal, index) => (
            <article key={signal.title} className="problem-card framed-panel">
              <span className="problem-card__index mono-text">0{index + 1}</span>
              <h3>{signal.title}</h3>
              <p>{signal.body}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
