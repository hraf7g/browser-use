'use client';

import { useEffect, useMemo, useState } from 'react';

type CursorPoint = {
  x: number;
  y: number;
};

type SignalCard = {
  id: string;
  label: string;
  title: string;
  detail: string;
  metric: string;
  position: CursorPoint;
};

const signalCards: SignalCard[] = [
  {
    id: 'source-scan',
    label: 'Source scan',
    title: 'Dubai Municipality procurement feed',
    detail: 'New civil maintenance opportunity parsed and normalized in both Arabic and English.',
    metric: 'Feed live · 02:14 UTC',
    position: { x: 18, y: 20 },
  },
  {
    id: 'fit-score',
    label: 'Fit score',
    title: '87% supplier profile match',
    detail: 'Matched against sector scope, tender keywords, budget pattern, and language requirements.',
    metric: 'High-fit opportunity',
    position: { x: 58, y: 18 },
  },
  {
    id: 'bilingual-brief',
    label: 'Bilingual brief',
    title: 'Specification normalized instantly',
    detail: 'Key dates, scope, qualification criteria, and issuer notes extracted into a structured brief.',
    metric: 'AR ↔ EN normalized',
    position: { x: 12, y: 62 },
  },
  {
    id: 'alert-route',
    label: 'Alert route',
    title: 'Signal sent to commercial team',
    detail: 'High-fit tender pushed to the relevant team with deadline risk highlighted and owner assigned.',
    metric: '3 minute response path',
    position: { x: 56, y: 60 },
  },
];

const cursorPath: CursorPoint[] = [
  { x: 16, y: 18 },
  { x: 27, y: 25 },
  { x: 60, y: 22 },
  { x: 70, y: 34 },
  { x: 48, y: 46 },
  { x: 20, y: 66 },
  { x: 58, y: 64 },
  { x: 74, y: 48 },
];

const tickDurationMs = 2200;

function formatCoordinate(value: number) {
  return `${value}%`;
}

export default function HomepageHeroVisual() {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    const interval = window.setInterval(() => {
      setActiveIndex((current) => (current + 1) % cursorPath.length);
    }, tickDurationMs);

    return () => window.clearInterval(interval);
  }, []);

  const activePoint = cursorPath[activeIndex] ?? cursorPath[0];
  const activeCard = signalCards[activeIndex % signalCards.length] ?? signalCards[0];

  const route = useMemo(() => {
    return cursorPath.map((point) => `${point.x},${point.y}`).join(' ');
  }, []);

  return (
    <div className="hero-visual framed-panel" aria-hidden="true">
      <div className="hero-visual__glow" />
      <div className="hero-visual__grid" />

      <svg className="hero-visual__route" viewBox="0 0 100 100" preserveAspectRatio="none">
        <polyline className="hero-visual__route-line" points={route} pathLength={100} />
      </svg>

      <div className="hero-visual__eyebrow mono-text">AUTONOMOUS TENDER SIGNAL LAYER</div>

      {signalCards.map((card) => {
        const isActive = card.id === activeCard.id;
        return (
          <article
            key={card.id}
            className={`hero-signal-card${isActive ? ' is-active' : ''}`}
            style={{
              left: formatCoordinate(card.position.x),
              top: formatCoordinate(card.position.y),
            }}
          >
            <span className="hero-signal-card__label mono-text">{card.label}</span>
            <h3>{card.title}</h3>
            <p>{card.detail}</p>
            <strong className="mono-text">{card.metric}</strong>
          </article>
        );
      })}

      <div className="hero-status-rail framed-panel">
        <div className="hero-status-rail__header">
          <span className="mono-text">Signal status</span>
          <span className="hero-status-rail__pulse" />
        </div>
        <div className="hero-status-rail__metric-row">
          <div>
            <span className="mono-text">Active watchlists</span>
            <strong>24</strong>
          </div>
          <div>
            <span className="mono-text">Critical deadlines</span>
            <strong>03</strong>
          </div>
        </div>
        <div className="hero-status-rail__current">
          <span className="mono-text">Current action</span>
          <strong>{activeCard.metric}</strong>
        </div>
      </div>

      <div
        className="hero-cursor"
        style={{ left: formatCoordinate(activePoint.x), top: formatCoordinate(activePoint.y) }}
      >
        <div className="hero-cursor__dot" />
        <div className="hero-cursor__ring" />
      </div>
    </div>
  );
}
