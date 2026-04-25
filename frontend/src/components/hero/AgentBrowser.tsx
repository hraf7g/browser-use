'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import AgentCursor from '@/components/hero/AgentCursor';
import { useReducedMotion } from '@/lib/useReducedMotion';

type TenderRow = {
  id: string;
  tenderNumber: string;
  entity: string;
  category: string;
  closingDate: string;
  estimatedValue: string;
};

type Point = {
  x: number;
  y: number;
};

type StoryState = {
  cursor: Point;
  clicking: boolean;
  scanProgress: number;
  rowFocused: boolean;
  cardVisible: boolean;
  scoreVisible: boolean;
  alertVisible: boolean;
  shimmerVisible: boolean;
  hoveredSource: boolean;
};

const tenderRows: TenderRow[] = [
  {
    id: 'row-1',
    tenderNumber: 'DW-2026-184',
    entity: 'بلدية دبي',
    category: 'خدمات استشارية',
    closingDate: '٢٨ مايو ٢٠٢٦',
    estimatedValue: '١.٨ مليون درهم',
  },
  {
    id: 'row-2',
    tenderNumber: 'AD-441-26',
    entity: 'دائرة الطاقة - أبوظبي',
    category: 'تقنية المعلومات',
    closingDate: '٣ يونيو ٢٠٢٦',
    estimatedValue: '٣.٢ مليون درهم',
  },
  {
    id: 'row-3',
    tenderNumber: 'INF-9021',
    entity: 'هيئة الطرق والمواصلات',
    category: 'مشاريع بنية تحتية',
    closingDate: '١٥ يونيو ٢٠٢٦',
    estimatedValue: '١٢.٤ مليون درهم',
  },
  {
    id: 'row-4',
    tenderNumber: 'KSA-7720',
    entity: 'أمانة منطقة الرياض',
    category: 'خدمات تشغيلية',
    closingDate: '٢٠ يونيو ٢٠٢٦',
    estimatedValue: '٥.١ مليون ريال',
  },
  {
    id: 'row-5',
    tenderNumber: 'QA-1290',
    entity: 'وزارة البلدية - قطر',
    category: 'توريد معدات',
    closingDate: '٢٤ يونيو ٢٠٢٦',
    estimatedValue: '٢.٦ مليون ريال',
  },
  {
    id: 'row-6',
    tenderNumber: 'OM-6135',
    entity: 'وزارة النقل - عُمان',
    category: 'صيانة الطرق',
    closingDate: '٣٠ يونيو ٢٠٢٦',
    estimatedValue: '٤.٩ مليون ريال',
  },
];

const sourceItems = ['Dubai eSupply', 'Etimad KSA', 'Abu Dhabi Procurement', 'Qatar Tenders'];
const rowFocusId = 'row-3';
const loopDurationMs = 9400;
const enterEnd = 1600;
const hoverEnd = 1960;
const clickEnd = 2260;
const moveEnd = 4660;
const focusEnd = 5600;
const cardEnd = 6500;
const scoreEnd = 7400;
const alertEnd = 8600;

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function cubicBezierLike(progress: number) {
  return progress < 0.5
    ? 4 * progress * progress * progress
    : 1 - Math.pow(-2 * progress + 2, 3) / 2;
}

function interpolate(from: number, to: number, progress: number) {
  return from + (to - from) * progress;
}

function createArcPoint(start: Point, end: Point, progress: number, arcHeight: number) {
  return {
    x: interpolate(start.x, end.x, progress),
    y: interpolate(start.y, end.y, progress) - Math.sin(progress * Math.PI) * arcHeight,
  };
}

function moveWithApproach(start: Point, end: Point, rawProgress: number, arcHeight: number) {
  const progress = clamp(rawProgress, 0, 1);
  const distance = Math.hypot(end.x - start.x, end.y - start.y);
  const slowApproachRatio = distance <= 80 ? 0.72 : (distance - 80) / distance;

  if (progress <= slowApproachRatio) {
    const fastProgress = cubicBezierLike(progress / slowApproachRatio) * 0.84;
    return createArcPoint(start, end, fastProgress, arcHeight);
  }

  const approachProgress = (progress - slowApproachRatio) / Math.max(1 - slowApproachRatio, 0.0001);
  const easedApproach = 0.84 + cubicBezierLike(approachProgress) * 0.16;
  return createArcPoint(start, end, easedApproach, arcHeight * 0.5);
}

function addCursorDrift(point: Point, elapsedMs: number, amplitude = 1.6) {
  return {
    x: point.x + Math.sin(elapsedMs / 145) * amplitude,
    y: point.y + Math.cos(elapsedMs / 185) * amplitude * 0.75,
  };
}

function getStoryState(elapsedMs: number): StoryState {
  const time = elapsedMs % loopDurationMs;
  const sourceTarget = { x: 110, y: 146 };
  const tableStart = { x: 320, y: 156 };
  const tableMid = { x: 362, y: 252 };
  const rowTarget = { x: 394, y: 298 };
  const alertTarget = { x: 602, y: 48 };
  const exitTarget = { x: 736, y: 26 };

  let cursor = { x: -84, y: 24 };
  let clicking = false;
  let scanProgress = 0;
  let rowFocused = false;
  let cardVisible = false;
  let scoreVisible = false;
  let alertVisible = false;
  let shimmerVisible = false;
  let hoveredSource = false;

  if (time < enterEnd) {
    cursor = moveWithApproach({ x: -84, y: 10 }, sourceTarget, time / enterEnd, 34);
  } else if (time < hoverEnd) {
    cursor = addCursorDrift(sourceTarget, time, 1.4);
    hoveredSource = true;
  } else if (time < clickEnd) {
    cursor = addCursorDrift(sourceTarget, time, 0.85);
    hoveredSource = true;
    clicking = time - hoverEnd <= 220;
    shimmerVisible = true;
  } else if (time < moveEnd) {
    const progress = (time - clickEnd) / (moveEnd - clickEnd);
    const midpointProgress = progress < 0.52 ? progress / 0.52 : (progress - 0.52) / 0.48;
    cursor =
      progress < 0.52
        ? moveWithApproach(sourceTarget, tableStart, midpointProgress, 22)
        : moveWithApproach(tableStart, tableMid, midpointProgress, 18);
    scanProgress = clamp((time - clickEnd - 220) / 1800, 0, 1);
    shimmerVisible = time - clickEnd < 500;
  } else if (time < focusEnd) {
    cursor = moveWithApproach(tableMid, rowTarget, (time - moveEnd) / (focusEnd - moveEnd), 14);
    scanProgress = 1;
    rowFocused = time > moveEnd + 220;
  } else if (time < cardEnd) {
    cursor = addCursorDrift(rowTarget, time, 1.2);
    scanProgress = 1;
    rowFocused = true;
    cardVisible = true;
  } else if (time < scoreEnd) {
    cursor = addCursorDrift({ x: rowTarget.x + 18, y: rowTarget.y - 22 }, time, 0.95);
    scanProgress = 1;
    rowFocused = true;
    cardVisible = true;
    scoreVisible = true;
  } else if (time < alertEnd) {
    cursor = moveWithApproach({ x: rowTarget.x + 18, y: rowTarget.y - 22 }, alertTarget, (time - scoreEnd) / (alertEnd - scoreEnd), 16);
    scanProgress = 1;
    rowFocused = true;
    cardVisible = true;
    scoreVisible = true;
    alertVisible = time > scoreEnd + 280;
  } else {
    cursor = moveWithApproach(alertTarget, exitTarget, (time - alertEnd) / (loopDurationMs - alertEnd), 14);
    scanProgress = 1;
    rowFocused = true;
    cardVisible = true;
    scoreVisible = true;
    alertVisible = true;
  }

  return {
    cursor,
    clicking,
    scanProgress,
    rowFocused,
    cardVisible,
    scoreVisible,
    alertVisible,
    shimmerVisible,
    hoveredSource,
  };
}

export default function AgentBrowser() {
  const prefersReducedMotion = useReducedMotion();
  const reducedMotionElapsedMs = clickEnd + 120;
  const [elapsedMs, setElapsedMs] = useState(reducedMotionElapsedMs);
  const animationFrameRef = useRef<number | null>(null);
  const startTimeRef = useRef<number | null>(null);

  useEffect(() => {
    if (prefersReducedMotion) {
      startTimeRef.current = null;
      if (animationFrameRef.current !== null) {
        window.cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
      return undefined;
    }

    const tick = (timestamp: number) => {
      if (startTimeRef.current === null) {
        startTimeRef.current = timestamp;
      }

      setElapsedMs(timestamp - startTimeRef.current);
      animationFrameRef.current = window.requestAnimationFrame(tick);
    };

    animationFrameRef.current = window.requestAnimationFrame(tick);

    return () => {
      if (animationFrameRef.current !== null) {
        window.cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [prefersReducedMotion]);

  const effectiveElapsedMs = prefersReducedMotion ? reducedMotionElapsedMs : elapsedMs;
  const storyState = useMemo(() => getStoryState(effectiveElapsedMs), [effectiveElapsedMs]);

  return (
    <div className="agent-browser-shell content-card" aria-label="محاكاة لوكيل يتصفح منصة مناقصات حكومية">
      <div className="agent-browser-frame">
        <div className="agent-browser-chrome">
          <div className="agent-browser-controls" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
          <div className="agent-browser-address">portal.tenderwatch.ai / source-monitoring / dubai-esupply</div>
          <div className="agent-browser-status">نشط</div>
        </div>

        <div className="agent-browser-body">
          <aside className="agent-browser-sidebar">
            <div className="agent-browser-sidebar__title">المصادر الرسمية</div>
            <ul className="agent-browser-sources">
              {sourceItems.map((source, index) => (
                <li
                  key={source}
                  className={index === 0 ? 'is-active' : undefined}
                  data-hovered={index === 0 && storyState.hoveredSource}
                >
                  <span className="agent-browser-source__dot" />
                  <span>{source}</span>
                </li>
              ))}
            </ul>
          </aside>

          <div className="agent-browser-content">
            <div className="agent-browser-toolbar">
              <div>
                <strong>Dubai eSupply</strong>
                <span>آخر مزامنة: منذ ٣ دقائق</span>
              </div>
              <div className="agent-browser-toolbar__badge">فحص مباشر</div>
            </div>

            <div className={`agent-browser-table-wrap${storyState.shimmerVisible ? ' is-shimmering' : ''}`}>
              <div
                aria-hidden="true"
                className="agent-browser-scanline"
                style={{ transform: `translateY(${44 + storyState.scanProgress * 224}px)` }}
              />

              <table className="agent-browser-table">
                <thead>
                  <tr>
                    <th>رقم المناقصة</th>
                    <th>الجهة الحكومية</th>
                    <th>الفئة</th>
                    <th>تاريخ الإغلاق</th>
                    <th>القيمة التقديرية</th>
                  </tr>
                </thead>
                <tbody>
                  {tenderRows.map((row) => {
                    const isFocused = row.id === rowFocusId && storyState.rowFocused;

                    return (
                      <tr key={row.id} className={isFocused ? 'is-focused' : undefined}>
                        <td>{row.tenderNumber}</td>
                        <td>{row.entity}</td>
                        <td>{row.category}</td>
                        <td>{row.closingDate}</td>
                        <td>{row.estimatedValue}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className={`agent-browser-card${storyState.cardVisible ? ' is-visible' : ''}`}>
            <span className="agent-browser-card__eyebrow">بطاقة مناقصة</span>
            <strong>تحديث طريق الخوانيج والبنية المحيطة</strong>
            <dl>
              <div>
                <dt>عنوان المناقصة</dt>
                <dd>تحديث طريق الخوانيج والبنية المحيطة</dd>
              </div>
              <div>
                <dt>الجهة</dt>
                <dd>هيئة الطرق والمواصلات</dd>
              </div>
              <div>
                <dt>تاريخ الإغلاق</dt>
                <dd>١٥ يونيو ٢٠٢٦</dd>
              </div>
              <div>
                <dt>القيمة</dt>
                <dd>١٢.٤ مليون درهم</dd>
              </div>
            </dl>
            <div className={`agent-browser-score${storyState.scoreVisible ? ' is-visible' : ''}`}>
              <span className="agent-browser-score__dot" />
              مطابقة ٩٢٪
            </div>
          </div>
        </div>

        <div className={`agent-browser-alert${storyState.alertVisible ? ' is-visible' : ''}`}>
          <span className="agent-browser-alert__pulse" />
          تنبيه جديد
        </div>

        <div className="agent-browser-caption">
          <span className="agent-browser-caption__status">{prefersReducedMotion ? 'وضع ثابت' : 'وضع تفاعلي'}</span>
          <p>
            وكيل المتصفح يراقب بوابات الشراء الرسمية، يقرأ الصفوف بتدرج بصري هادئ، ثم يستخرج
            فرصة متوافقة ويرسل تنبيهاً فورياً للفريق.
          </p>
        </div>

        {!prefersReducedMotion ? (
          <>
            <AgentCursor x={storyState.cursor.x} y={storyState.cursor.y} clicking={storyState.clicking} />
            <span
              aria-hidden="true"
              className={`agent-browser-click-ripple${storyState.clicking ? ' is-visible' : ''}`}
              style={{ left: `${storyState.cursor.x + 8}px`, top: `${storyState.cursor.y + 18}px` }}
            />
          </>
        ) : null}
      </div>
    </div>
  );
}
