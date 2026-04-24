const activityFeed = [
  {
    time: '16:02',
    title: 'New utilities tender detected',
    detail: 'ADDC maintenance package captured and classified under infrastructure operations.',
    state: 'new-signal',
  },
  {
    time: '16:05',
    title: 'Fit score upgraded to high confidence',
    detail: 'Historic scope similarity and geography profile increased routing priority.',
    state: 'fit-score',
  },
  {
    time: '16:09',
    title: 'Arabic qualification note translated',
    detail: 'Mandatory vendor registration and insurance clauses flagged for review.',
    state: 'translation',
  },
  {
    time: '16:11',
    title: 'Commercial owner assigned',
    detail: 'Opportunity routed with summary, deadline status, and next recommended action.',
    state: 'routed',
  },
] as const;

const activityStats = [
  { label: 'Signals today', value: '128' },
  { label: 'High-fit matches', value: '19' },
  { label: 'At-risk deadlines', value: '04' },
] as const;

export default function LiveActivityPreview() {
  return (
    <section className="section-shell" id="activity">
      <div className="section-inner activity-layout">
        <div className="activity-copy">
          <span className="section-label">Live activity preview</span>
          <h2 className="section-title">A control surface for what just changed, what matters, and who should move.</h2>
          <p className="section-lead">
            The interface is designed to feel alive. Instead of static records, teams see a moving stream
            of monitored issuer activity, qualification changes, translation events, and routed actions.
          </p>

          <div className="activity-stats">
            {activityStats.map((stat) => (
              <div key={stat.label} className="activity-stat framed-panel">
                <span className="mono-text">{stat.label}</span>
                <strong>{stat.value}</strong>
              </div>
            ))}
          </div>
        </div>

        <div className="activity-panel framed-panel">
          <div className="activity-panel__header">
            <div>
              <span className="mono-text">Live watchtower</span>
              <strong>Recent operating events</strong>
            </div>
            <span className="activity-panel__badge mono-text">Streaming</span>
          </div>

          <div className="activity-feed" aria-label="Recent tender activity">
            {activityFeed.map((item) => (
              <article key={`${item.time}-${item.title}`} className="activity-item">
                <div className="activity-item__time mono-text">{item.time}</div>
                <div className={`activity-item__state activity-item__state--${item.state}`} />
                <div className="activity-item__body">
                  <h3>{item.title}</h3>
                  <p>{item.detail}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
