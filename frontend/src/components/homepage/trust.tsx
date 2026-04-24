const trustPoints = [
  'Built for enterprise procurement and public-sector response workflows',
  'Structured around bilingual GCC tender realities, not generic lead feeds',
  'Designed to create confidence before routing decisions are made',
] as const;

const trustMetrics = [
  { value: 'Enterprise-ready', label: 'built for procurement rigor and team coordination' },
  { value: 'Signal-first', label: 'focus on actionable change, not static listings' },
  { value: 'Bilingual-native', label: 'Arabic and English operating context together' },
] as const;

export default function Trust() {
  return (
    <section className="section-shell" id="trust">
      <div className="section-inner trust-layout framed-panel">
        <div className="trust-copy">
          <span className="section-label">Why teams can trust the system</span>
          <h2 className="section-title">Clarity, timing, and operational confidence built into the experience.</h2>
          <p className="section-lead">
            The strongest procurement platforms do more than collect data. They help teams trust the
            signal, understand why it matters, and move with less hesitation. Tender Watch is being shaped
            around that standard.
          </p>

          <ul className="trust-points">
            {trustPoints.map((point) => (
              <li key={point}>{point}</li>
            ))}
          </ul>
        </div>

        <div className="trust-metrics">
          {trustMetrics.map((metric) => (
            <div key={metric.label} className="trust-metric">
              <strong>{metric.value}</strong>
              <span>{metric.label}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
