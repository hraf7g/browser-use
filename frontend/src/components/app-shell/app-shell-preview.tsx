'use client';

import { useTranslation } from '@/context/language-context';
import { motion } from 'framer-motion';

const previewStats = [
	{ key: 'active', value: '124' },
	{ key: 'matched', value: '12' },
	{ key: 'sources', value: '54' },
] as const;

const previewStages = [
	{ key: 'sourceChecked', time: '2m' },
	{ key: 'tenderDetected', time: '4m' },
	{ key: 'matchCreated', time: '6m' },
	{ key: 'alertSent', time: '7m' },
	{ key: 'briefDelivered', time: '18m' },
] as const;

const sourceHealthRows = [
	{ label: 'Official source 01', status: 'healthy', pulseClass: 'bg-emerald-500' },
	{ label: 'Official source 02', status: 'checking', pulseClass: 'bg-blue-500' },
	{ label: 'Official source 03', status: 'delayed', pulseClass: 'bg-amber-500' },
] as const;

export default function AppShellPreview() {
  const { t } = useTranslation();

  return (
    <motion.div
      className="space-y-8 p-4 lg:p-8"
      initial="hidden"
      animate="show"
      variants={{
        hidden: { opacity: 0 },
        show: {
          opacity: 1,
          transition: { staggerChildren: 0.08, delayChildren: 0.05 },
        },
      }}
    >
      <motion.section
        className="space-y-2"
        variants={{
          hidden: { opacity: 0, y: 12 },
          show: { opacity: 1, y: 0 },
        }}
      >
        <p className="text-xs font-semibold uppercase tracking-[0.28em] text-slate-500 dark:text-slate-400">
          Workspace preview
        </p>
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-2xl space-y-3">
            <h2 className="text-3xl font-bold tracking-tight text-slate-950 dark:text-white lg:text-4xl">
              {t.app.preview.activityTitle}
            </h2>
            <p className="max-w-xl text-sm leading-6 text-slate-600 dark:text-slate-400">
              A compact operator surface for source checks, tender matches, and brief delivery.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-300">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            Monitoring live
          </div>
        </div>
      </motion.section>

      <motion.div
        className="grid grid-cols-1 gap-4 md:grid-cols-3"
        variants={{
          hidden: { opacity: 0 },
          show: { opacity: 1 },
        }}
      >
        {previewStats.map((stat) => (
          <div
            key={stat.key}
            className="rounded-3xl border border-slate-200 bg-white/90 p-5 shadow-sm backdrop-blur dark:border-slate-800 dark:bg-slate-900/90"
          >
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">
              {t.app.preview.stats[stat.key]}
            </p>
            <p className="mt-4 text-3xl font-bold tracking-tight text-slate-950 dark:text-white">
              {stat.value}
            </p>
          </div>
        ))}
      </motion.div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.45fr_0.85fr]">
        <motion.section
          className="rounded-[28px] border border-slate-200 bg-white/90 p-6 shadow-sm backdrop-blur dark:border-slate-800 dark:bg-slate-900/90"
          variants={{
            hidden: { opacity: 0, y: 16 },
            show: { opacity: 1, y: 0 },
          }}
        >
          <div className="flex items-center justify-between gap-4 border-b border-slate-200 pb-4 dark:border-slate-800">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">
                Processing line
              </p>
              <h3 className="mt-1 text-lg font-semibold text-slate-950 dark:text-white">
                Current brief generation
              </h3>
            </div>
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">
              Five-stage flow
            </p>
          </div>

          <div className="mt-6 space-y-4">
            {previewStages.map((stage, index) => (
              <motion.div
                key={stage.key}
                className="flex gap-4"
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.12 + index * 0.06 }}
              >
                <div className="relative flex shrink-0 items-start justify-center">
                  <span className="mt-1 flex h-7 w-7 items-center justify-center rounded-full border border-slate-200 bg-slate-50 text-[11px] font-bold text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200">
                    {index + 1}
                  </span>
                  {index !== previewStages.length - 1 ? (
                    <span className="absolute top-8 h-[calc(100%-0.5rem)] w-px bg-slate-200 dark:bg-slate-800" />
                  ) : null}
                </div>
                <div className="min-w-0 flex-1 pb-4">
                  <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                    <p className="text-sm font-semibold text-slate-950 dark:text-white">
                      {t.app.preview.status[stage.key]}
                    </p>
                    <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                      {stage.time} ago
                    </p>
                  </div>
                  <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                    <motion.div
                      className="h-full rounded-full bg-gradient-to-r from-blue-600 via-cyan-500 to-emerald-500"
                      initial={{ width: 0 }}
                      animate={{ width: `${64 + index * 6}%` }}
                      transition={{ duration: 0.7, delay: 0.16 + index * 0.05 }}
                    />
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.section>

        <motion.aside
          className="rounded-[28px] border border-slate-200 bg-slate-950 p-6 text-slate-50 shadow-sm dark:border-slate-800"
          variants={{
            hidden: { opacity: 0, y: 16 },
            show: { opacity: 1, y: 0 },
          }}
        >
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">
                Source health
              </p>
              <h3 className="mt-1 text-lg font-semibold text-white">
                Monitoring snapshot
              </h3>
            </div>
            <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-400 shadow-[0_0_0_6px_rgba(74,222,128,0.12)]" />
          </div>

          <div className="mt-6 space-y-3">
            {sourceHealthRows.map((row, index) => (
              <motion.div
                key={row.label}
                className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.14 + index * 0.05 }}
              >
                <div className="flex items-center gap-3">
                  <span className={`h-2.5 w-2.5 rounded-full ${row.pulseClass}`} />
                  <div>
                    <p className="text-sm font-semibold text-white">
                      {row.label}
                    </p>
                    <p className="text-xs text-slate-400">
                      {t.app.preview.activityTitle}
                    </p>
                  </div>
                </div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-300">
                  {t.activity.monitoringStatus[row.status as keyof typeof t.activity.monitoringStatus]}
                </p>
              </motion.div>
            ))}
          </div>

          <div className="mt-6 rounded-3xl border border-white/10 bg-gradient-to-br from-white/8 to-white/3 p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">
              Delivery state
            </p>
            <p className="mt-2 text-2xl font-bold tracking-tight text-white">
              Brief ready
            </p>
            <p className="mt-2 text-sm leading-6 text-slate-300">
              The latest match set has already been filtered, staged, and queued for delivery.
            </p>
          </div>
        </motion.aside>
      </div>
    </motion.div>
  );
}
