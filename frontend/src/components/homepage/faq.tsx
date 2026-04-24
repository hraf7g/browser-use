const faqItems = [
  {
    question: 'What does Tender Watch actually do?',
    answer:
      'Tender Watch monitors tender sources, structures messy procurement notices into decision-ready briefs, scores fit, and routes high-confidence opportunities to the right team.',
  },
  {
    question: 'Is this focused on GCC and bilingual procurement workflows?',
    answer:
      'Yes. The experience is being designed around Arabic and English tender analysis, public-sector procurement realities, and the timing pressure common in regional bid environments.',
  },
  {
    question: 'Is it a database or a live operating layer?',
    answer:
      'The direction is a live operating layer. The goal is not just to store tenders, but to monitor change, qualify relevance, and support faster internal action.',
  },
  {
    question: 'Who is this for inside an organization?',
    answer:
      'Commercial teams, bid managers, proposal teams, and leadership all benefit because the product is built around shared visibility and routed ownership.',
  },
] as const;

export default function Faq() {
  return (
    <section className="section-shell" id="faq">
      <div className="section-inner faq-layout">
        <div className="faq-copy">
          <span className="section-label">Common questions</span>
          <h2 className="section-title">A premium story still needs clear answers.</h2>
          <p className="section-lead">
            The best landing pages reduce uncertainty at the end of the scroll. This section keeps that
            discipline — direct questions, concise answers, and no decorative filler.
          </p>
        </div>

        <div className="faq-list">
          {faqItems.map((item) => (
            <article key={item.question} className="faq-item framed-panel">
              <h3>{item.question}</h3>
              <p>{item.answer}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
