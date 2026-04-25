import Navbar from '@/components/layout/Navbar';
import HeroSection from '@/components/hero/HeroSection';
import HowItWorks from '@/components/sections/HowItWorks';
import BilingualPanel from '@/components/sections/BilingualPanel';
import LiveActivity from '@/components/sections/LiveActivity';
import ProductPreview from '@/components/sections/ProductPreview';
import FinalCTA from '@/components/sections/FinalCTA';

export default function HomePage() {
  return (
    <div className="homepage-shell" id="top">
      <Navbar />
      <main className="homepage-main">
        <HeroSection />
        <HowItWorks />
        <BilingualPanel />
        <LiveActivity />
        <ProductPreview />
        <FinalCTA />
      </main>
    </div>
  );
}
