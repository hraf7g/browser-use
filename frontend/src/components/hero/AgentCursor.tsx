'use client';

import React from 'react';
import { useTranslation } from '@/context/language-context';
import { motion } from 'framer-motion';

interface AgentCursorProps {
  x: number;
  y: number;
  isClicking: boolean;
}

const AgentCursor: React.FC<AgentCursorProps> = ({ x, y, isClicking }) => {
  const { t } = useTranslation();
  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        pointerEvents: 'none',
        zIndex: 100,
        transition: 'transform 0.15s ease-out',
      }}
    >
      {/* Click Ripple */}
      <AnimatePresence>
        {isClicking && (
          <motion.div
            initial={{ scale: 0, opacity: 0.5 }}
            animate={{ scale: 2, opacity: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
            className="absolute -translate-x-1/2 -translate-y-1/2 w-10 h-10 bg-primary/40 rounded-full"
          />
        )}
      </AnimatePresence>

      {/* Main Cursor SVG */}
      <div className="relative -translate-x-[2px] -translate-y-[2px]">
        <svg
          width="24"
          height="24"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="drop-shadow-lg"
        >
          <path
            d="M3 3L10.07 19.97L12.58 12.58L19.97 10.07L3 3Z"
            fill="white"
            stroke="black"
            strokeWidth="1.5"
            strokeLinejoin="round"
          />
          <circle cx="16" cy="16" r="3" fill="#1E5FC5" className="animate-pulse" />
        </svg>
        
        {/* Agent Label */}
        <div className="absolute left-7 top-7 bg-primary text-white text-[10px] px-1.5 py-0.5 rounded shadow-sm whitespace-nowrap font-bold">
          {t.agentSimulation.cursorLabel}
        </div>
      </div>
    </div>
  );
};

import { AnimatePresence } from 'framer-motion';

export default AgentCursor;
