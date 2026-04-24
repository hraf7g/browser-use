'use client';

import Header from '@/components/homepage/header';
import Hero from '@/components/homepage/hero';
import Problem from '@/components/homepage/problem';
import Trust from '@/components/homepage/trust';
import HowItWorks from '@/components/homepage/how-it-works';
import BilingualAnalysis from '@/components/homepage/bilingual-analysis';
import LiveActivityPreview from '@/components/homepage/live-activity-preview';
import ProductPreview from '@/components/homepage/product-preview';
import FinalCTA from '@/components/homepage/final-cta';
import Footer from '@/components/homepage/footer';

export default function HomepageExperience() {
  return (
    <div className="relative overflow-x-clip bg-white text-slate-950 dark:bg-slate-950 dark:text-white">
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[720px] bg-[radial-gradient(circle_at_top,rgba(59,130,246,0.14),transparent_48%)]" />
      <div className="pointer-events-none absolute inset-x-0 top-80 -z-10 h-[640px] bg-[radial-gradient(circle_at_center,rgba(16,185,129,0.08),transparent_52%)]" />
      <Header />
      <main>
        <Hero />
        <Trust />
        <Problem />
        <HowItWorks />
        <ProductPreview />
        <BilingualAnalysis />
        <LiveActivityPreview />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  );
}
