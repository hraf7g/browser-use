import Header from '@/components/homepage/header';
import Hero from '@/components/homepage/hero';
import HowItWorks from '@/components/homepage/how-it-works';
import BilingualAnalysis from '@/components/homepage/bilingual-analysis';
import LiveActivityPreview from '@/components/homepage/live-activity-preview';
import ProductPreview from '@/components/homepage/product-preview';
import FinalCTA from '@/components/homepage/final-cta';
import Footer from '@/components/homepage/footer';

export default function HomePage() {
  return (
    <div className="relative">
      <Header />
      {/* 1. Hero */}
      <Hero />
      {/* 2. What Tender Watch does */}
      <HowItWorks />
      {/* 3. Built for MENA procurement */}
      <BilingualAnalysis />
      {/* 4. Live activity */}
      <LiveActivityPreview />
      {/* 5. Why teams use it + Product preview */}
      <ProductPreview />
      {/* 6. Final CTA */}
      <FinalCTA />
      <Footer />
    </div>
  );
}
