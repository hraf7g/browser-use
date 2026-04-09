'use client';

import type { InputHTMLAttributes } from 'react';

type InputGroupProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
};

export default function InputGroup({ label, className = '', ...props }: InputGroupProps) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">
        {label}
      </label>
      <input
        {...props}
        className={`w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 dark:border-slate-800 dark:bg-slate-900 ${className}`}
      />
    </div>
  );
}
