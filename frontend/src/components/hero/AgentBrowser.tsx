'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import AgentCursor from './AgentCursor';
import { useReducedMotion } from '@/lib/useReducedMotion';
import { useTranslation } from '@/context/language-context';



const AgentBrowser = () => {
  const { t, dir } = useTranslation();
  const shouldReduceMotion = useReducedMotion();
  const [cursorPos, setCursorPos] = useState({ x: -100, y: -100 });
  const [isClicking, setIsClicking] = useState(false);
  const [activeRow, setActiveRow] = useState<number | null>(null);
  const [showCard, setShowCard] = useState(false);
  const [scanningRow, setScanningRow] = useState<number | null>(null);
  const [alertPulse, setAlertPulse] = useState(false);
  
  const containerRef = useRef<HTMLDivElement>(null);
  const requestRef = useRef<number>(0);
  const startTimeRef = useRef<number>(0);

  // Animation cycle durations (ms)
  const CYCLE_DURATION = 10000;

  const animate = (time: number) => {
    if (!startTimeRef.current) startTimeRef.current = time;
    const elapsed = (time - startTimeRef.current) % CYCLE_DURATION;
    
    // Story Arc logic
    if (elapsed < 1500) {
      // 1. Enter and move to sidebar
      const progress = elapsed / 1500;
      const eased = cubicBezier(0.25, 0.1, 0.25, 1, progress);
      setCursorPos({ x: 50 + eased * 100, y: 150 + eased * 50 });
      setShowCard(false);
      setActiveRow(null);
      setScanningRow(null);
      setAlertPulse(false);
    } else if (elapsed < 2000) {
      // 2. Hover sidebar (pause)
      setCursorPos({ x: 150, y: 200 });
    } else if (elapsed < 2300) {
      // 3. Click sidebar
      setIsClicking(elapsed < 2150);
      setCursorPos({ x: 150, y: 200 });
    } else if (elapsed < 4000) {
      // 4. Move to table and scan
      const progress = (elapsed - 2300) / 1700;
      const eased = cubicBezier(0.25, 0.1, 0.25, 1, progress);
      setCursorPos({ x: 150 + eased * 200, y: 200 + eased * 100 });
      
      // Scanning effect
      if (elapsed > 2800) {
        const rowIdx = Math.floor((elapsed - 2800) / 300) % 5;
        setScanningRow(rowIdx);
      }
    } else if (elapsed < 5500) {
      // 5. Stop on row 3
      const progress = (elapsed - 4000) / 1500;
      const eased = cubicBezier(0.25, 0.1, 0.25, 1, progress);
      // Row 3 is at roughly y=260
      setCursorPos({ x: 350 + eased * 50, y: 250 + eased * 15 });
      setScanningRow(2);
      setActiveRow(2);
    } else if (elapsed < 6000) {
      // 6. Click row 3
      setIsClicking(elapsed < 5750);
      setCursorPos({ x: 400, y: 265 });
    } else if (elapsed < 9000) {
      // 7. Show card and alert
      setShowCard(true);
      setAlertPulse(elapsed > 7000);
    } else {
      // Fade out
      setShowCard(false);
    }

    requestRef.current = requestAnimationFrame(animate);
  };

  useEffect(() => {
    if (shouldReduceMotion) return;
    requestRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(requestRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shouldReduceMotion]);

  // Cubic Bezier helper
  function cubicBezier(p0: number, p1: number, p2: number, p3: number, t: number) {
    return Math.pow(1 - t, 3) * p0 + 3 * Math.pow(1 - t, 2) * t * p1 + 3 * (1 - t) * Math.pow(t, 2) * p2 + Math.pow(t, 3) * p3;
  }

  if (shouldReduceMotion) {
    return (
      <div className="w-full aspect-[4/3] bg-white dark:bg-navy-800 rounded-2xl border border-border overflow-hidden shadow-2xl flex items-center justify-center">
        <p className="text-muted text-sm">{t.agentSimulation.emptyState}</p>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      className="relative w-full aspect-[4/3] bg-white dark:bg-navy-900 rounded-2xl border border-border overflow-hidden shadow-2xl font-arabic"
      dir={dir}
    >
      {/* Browser UI */}
      <div className="absolute top-0 inset-x-0 h-10 bg-slate-50 dark:bg-navy-800 border-b border-border flex items-center px-4 gap-2">
        <div className="flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-red-400" />
          <div className="w-2.5 h-2.5 rounded-full bg-amber-400" />
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
        </div>
        <div className="mx-auto w-1/2 h-5 bg-white dark:bg-navy-900 rounded border border-border flex items-center px-3 text-[10px] text-muted truncate">
          https://esupply.dubai.gov.ae/portal/
        </div>
      </div>

      <div className="mt-10 flex h-full">
        {/* Sidebar */}
        <div className="w-40 border-l border-border bg-slate-50/50 dark:bg-navy-800/50 p-4 flex flex-col gap-3">
          <div className="h-2 w-full bg-slate-200 dark:bg-navy-700 rounded" />
          <div className={`h-8 w-full rounded flex items-center px-2 text-[10px] transition-colors ${cursorPos.x < 180 && cursorPos.y < 250 ? 'bg-primary/10 text-primary' : 'bg-transparent'}`}>
            Dubai eSupply
          </div>
          <div className="h-2 w-3/4 bg-slate-200 dark:bg-navy-700 rounded" />
          <div className="h-2 w-1/2 bg-slate-200 dark:bg-navy-700 rounded" />
        </div>

        {/* Main Content */}
        <div className="flex-1 p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-sm font-bold">{t.agentSimulation.activeTendersTitle}</h3>
            <div className={`w-3 h-3 rounded-full bg-primary transition-opacity ${alertPulse ? 'animate-ping' : 'opacity-0'}`} />
          </div>

          <div className="space-y-2">
            <div className="grid grid-cols-5 gap-4 pb-2 border-b border-border text-[9px] font-bold text-muted">
              <div>{t.agentSimulation.tableBuyer}</div>
              <div>{t.agentSimulation.tableCategory}</div>
              <div>{t.agentSimulation.tableCloseDate}</div>
              <div className="col-span-2 text-start">{t.agentSimulation.tableTitle}</div>
            </div>
            {t.agentSimulation.tenders.map((row, i) => (
              <div 
                key={row.id}
                className={`grid grid-cols-5 gap-4 py-2.5 px-2 rounded text-[10px] transition-all duration-300 relative ${
                  activeRow === i ? 'bg-primary/5 ring-1 ring-primary/20 scale-[1.02]' : 
                  scanningRow === i ? 'bg-slate-50 dark:bg-navy-800' : ''
                }`}
              >
                <div className="font-medium truncate">{row.source}</div>
                <div className="text-muted">{row.category}</div>
                <div className="text-muted">{row.date}</div>
                <div className="col-span-2 text-start font-semibold truncate">{row.title}</div>
                
                {/* Scan Indicator */}
                {scanningRow === i && (
                  <motion.div 
                    layoutId="scan-indicator"
                    className="absolute inset-x-0 -bottom-px h-px bg-primary shadow-[0_0_10px_rgba(30,95,197,0.5)]"
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Extracted Tender Card */}
      <AnimatePresence>
        {showCard && (
          <motion.div
            initial={{ opacity: 0, x: 20, scale: 0.9 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 20, scale: 0.9 }}
            className={`absolute top-1/2 ${dir === "rtl" ? "right-8" : "left-8"} -translate-y-1/2 w-64 bg-white dark:bg-navy-800 rounded-xl shadow-2xl border border-primary/20 p-5 z-20 overflow-hidden`}
          >
            <div className="absolute top-0 right-0 w-1 h-full bg-primary" />
            <div className="flex justify-between items-start mb-4">
              <span className="bg-emerald-500/10 text-emerald-600 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                {t.agentSimulation.matchBadge}
              </span>
              <span className="text-[10px] text-muted">{t.agentSimulation.tenderRef}</span>
            </div>
            <h4 className="text-xs font-bold mb-3 leading-relaxed">{t.agentSimulation.sampleTitle}</h4>
            <div className="space-y-2">
              <div className="flex justify-between text-[10px]">
                <span className="text-muted">{t.agentSimulation.sampleBuyer}</span>
                <span className="font-medium">DMT Abu Dhabi</span>
              </div>
              <div className="flex justify-between text-[10px]">
                <span className="text-muted">{t.agentSimulation.sampleBudget}</span>
                <span className="font-medium text-primary">{t.agentSimulation.sampleBudgetVal}</span>
              </div>
              <div className="flex justify-between text-[10px]">
                <span className="text-muted">{t.agentSimulation.sampleClose}</span>
                <span className="font-medium">{t.agentSimulation.sampleCloseVal}</span>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-border flex gap-2">
              <div className="flex-1 h-7 bg-primary rounded flex items-center justify-center text-white text-[10px] font-bold">{t.agentSimulation.btnAnalyze}</div>
              <div className="flex-1 h-7 bg-slate-100 dark:bg-navy-700 rounded flex items-center justify-center text-[10px] font-bold text-muted">{t.agentSimulation.btnSave}</div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Pulse Alert */}
      <AnimatePresence>
        {alertPulse && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="absolute top-14 left-1/2 -translate-x-1/2 bg-primary text-white text-[10px] font-bold px-4 py-2 rounded-full shadow-lg flex items-center gap-2 z-30"
          >
            <span className="w-2 h-2 bg-white rounded-full animate-ping" />
            {t.agentSimulation.alertMessage}
          </motion.div>
        )}
      </AnimatePresence>

      {/* The Agent Cursor */}
      <AgentCursor x={cursorPos.x} y={cursorPos.y} isClicking={isClicking} />
    </div>
  );
};

export default AgentBrowser;
