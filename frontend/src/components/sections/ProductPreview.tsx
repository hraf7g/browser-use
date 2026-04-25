'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { useTranslation } from '@/context/language-context';

const ProductPreview = () => {
  const { t, dir } = useTranslation();
  const containerRef = useRef<HTMLDivElement>(null);
  
  const x = useMotionValue(0);
  const y = useMotionValue(0);

  const mouseXSpring = useSpring(x);
  const mouseYSpring = useSpring(y);

  const rotateX = useTransform(mouseYSpring, [-0.5, 0.5], ["6deg", "-6deg"]);
  const rotateY = useTransform(mouseXSpring, [-0.5, 0.5], ["-6deg", "6deg"]);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const xPct = mouseX / width - 0.5;
    const yPct = mouseY / height - 0.5;
    x.set(xPct);
    y.set(yPct);
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  return (
    <section className="py-24 bg-white dark:bg-navy-900 overflow-hidden" dir={dir}>
      <div className="container mx-auto px-6 text-center mb-16">
        <h2 className="text-3xl md:text-4xl font-bold mb-4">{t.productPreviewHome.title}</h2>
        <p className="text-muted max-w-2xl mx-auto">{t.productPreviewHome.subtitle}</p>
      </div>

      <div 
        ref={containerRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        className="container mx-auto px-6 flex justify-center perspective-[1500px]"
      >
        <motion.div
          style={{
            rotateX,
            rotateY,
            transformStyle: "preserve-3d",
          }}
          className="w-full max-w-5xl bg-slate-100 dark:bg-navy-800 rounded-2xl border border-border shadow-[0_50px_100px_-20px_rgba(0,0,0,0.15)] dark:shadow-[0_50px_100px_-20px_rgba(0,0,0,0.5)] overflow-hidden flex flex-col md:flex-row h-[600px] relative"
        >
          {/* Sidebar */}
          <div className="w-full md:w-56 bg-white dark:bg-navy-900 border-border border-e p-6 flex flex-col gap-6 z-10">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-white font-bold text-sm">TW</div>
              <span className="font-bold text-sm">Tender Watch</span>
            </div>
            <div className="space-y-1">
                            {[
                { name: t.productPreviewHome.sidebar.tenders, icon: '📋', active: true },
                { name: t.productPreviewHome.sidebar.sources, icon: '🌐' },
                { name: t.productPreviewHome.sidebar.alerts, icon: '🔔' },
                { name: t.productPreviewHome.sidebar.activity, icon: '📈' },
                { name: t.productPreviewHome.sidebar.settings, icon: '⚙️' },
              ].map((item) => (
                <div 
                  key={item.name}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-bold transition-colors ${item.active ? 'bg-primary/10 text-primary' : 'text-muted hover:bg-slate-50 dark:hover:bg-navy-800'}`}
                >
                  <span className="text-lg">{item.icon}</span>
                  {item.name}
                </div>
              ))}
            </div>
          </div>

          {/* Main Area */}
          <div className="flex-1 flex flex-col bg-slate-50/50 dark:bg-navy-800/50 overflow-hidden">
            {/* Top Bar */}
            <div className="h-16 border-b border-border bg-white dark:bg-navy-900 px-6 flex items-center justify-between z-10">
              <div className="flex items-center gap-4 text-xs font-bold">
                <div className="flex items-center gap-2">
                  <span className="text-muted">{t.productPreviewHome.topbar.lastCheck}</span>
                  <span>{t.productPreviewHome.topbar.timeAgo}</span>
                </div>
                <div className="h-4 w-px bg-border" />
                <div className="flex items-center gap-2 text-success">
                  <span className="w-2 h-2 bg-success rounded-full animate-pulse" />
                  {t.productPreviewHome.topbar.systemStatus}
                </div>
              </div>
              <div className="w-8 h-8 bg-slate-200 dark:bg-navy-700 rounded-full" />
            </div>

            {/* Dashboard Content */}
            <div className="p-6 flex-1 overflow-auto">
              <div className="flex justify-between items-end mb-8">
                <div>
                  <h3 className="text-xl font-bold mb-1">{t.productPreviewHome.main.suggested}</h3>
                  <p className="text-xs text-muted">{t.productPreviewHome.main.basedOn}</p>
                </div>
                <div className="flex gap-2">
                  <div className="px-4 py-2 bg-white dark:bg-navy-900 border border-border rounded-lg text-xs font-bold">{t.productPreviewHome.main.filter}</div>
                  <div className="px-4 py-2 bg-primary text-white rounded-lg text-xs font-bold">{t.productPreviewHome.main.export}</div>
                </div>
              </div>

              <div className="space-y-3">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="bg-white dark:bg-navy-900 p-4 rounded-xl border border-border flex items-center gap-6 shadow-sm group hover:border-primary/30 transition-colors">
                    <div className="w-12 h-12 bg-slate-50 dark:bg-navy-800 rounded-lg flex items-center justify-center text-xl">📄</div>
                    <div className="flex-1">
                      <div className="text-sm font-bold mb-1">{t.productPreviewHome.main.tenderTitle}{i}</div>
                      <div className="flex gap-4 text-[10px] text-muted">
                        <span>{t.productPreviewHome.main.buyer}</span>
                        <span>{t.productPreviewHome.main.ref}{i}</span>
                      </div>
                    </div>
                    <div className="text-left">
                      <div className="text-xs font-bold text-primary mb-1">{t.productPreviewHome.main.match}{6-i}{t.productPreviewHome.main.percent}</div>
                      <div className="text-[10px] text-muted">{t.productPreviewHome.main.endsIn}{i}{t.productPreviewHome.main.may}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Floating Alert Card */}
          <motion.div 
            style={{ translateZ: "50px" }}
            className={`absolute top-20 ${dir === 'rtl' ? 'right-10' : 'left-10'} w-64 bg-primary text-white p-5 rounded-2xl shadow-2xl shadow-primary/40 z-20`}
          >
            <div className="flex justify-between items-start mb-3">
              <div className="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center">🔔</div>
              <div className="bg-white/20 text-[10px] font-bold px-2 py-0.5 rounded">{t.productPreviewHome.alert.now}</div>
            </div>
            <h4 className="text-sm font-bold mb-1">{t.productPreviewHome.alert.newAlert}</h4>
            <p className="text-xs text-white/80 mb-4">{t.productPreviewHome.alert.alertDesc}</p>
            <div className="h-8 bg-white text-primary rounded-lg flex items-center justify-center text-xs font-bold">{t.productPreviewHome.alert.viewDetails}</div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
};

export default ProductPreview;
