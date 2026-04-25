import Navbar from '@/components/layout/Navbar';
import HeroSection from '@/components/hero/HeroSection';
import HowItWorks from '@/components/sections/HowItWorks';
import BilingualPanel from '@/components/sections/BilingualPanel';
import LiveActivity from '@/components/sections/LiveActivity';
import ProductPreview from '@/components/sections/ProductPreview';
import FeaturesCoverage from '@/components/sections/FeaturesCoverage';
import FinalCTA from '@/components/sections/FinalCTA';
import Footer from '@/components/layout/Footer';

export default function HomePage() {
  return (
    <main className="relative min-h-screen bg-white dark:bg-navy-900 text-slate-900 dark:text-slate-50">
      <Navbar />
      
      {/* 1. Hero Section with AI Agent Animation */}
      <HeroSection />

      {/* 2. How it Works (4 Steps) */}
      <HowItWorks />

      {/* 3. Features & GCC Coverage */}
      <FeaturesCoverage />

      {/* 4. Bilingual Analysis Proof */}
      <BilingualPanel />

      {/* 4. Live Activity Feed */}
      <LiveActivity />

      {/* 5. Product Preview (3D Dashboard) */}
      <ProductPreview />

      {/* 6. Final Conversion CTA */}
      <FinalCTA />

      {/* Footer */}
      <Footer />
    </main>
  );
}
