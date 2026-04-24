import BilingualAnalysis from '@/components/homepage/bilingual-analysis';
import Faq from '@/components/homepage/faq';
import FinalCTA from '@/components/homepage/final-cta';
import Footer from '@/components/homepage/footer';
import Header from '@/components/homepage/header';
import Hero from '@/components/homepage/hero';
import HowItWorks from '@/components/homepage/how-it-works';
import LiveActivityPreview from '@/components/homepage/live-activity-preview';
import Offers from '@/components/homepage/offers';
import Problem from '@/components/homepage/problem';
import ProductPreview from '@/components/homepage/product-preview';
import Trust from '@/components/homepage/trust';

const homepageSectionOrder = [
  'hero',
  'problem',
  'how-it-works',
  'bilingual-analysis',
  'live-activity-preview',
  'product-preview',
  'offers',
  'trust',
  'faq',
  'final-cta',
] as const;

export default function HomepageExperience() {
  return (
    <div className="homepage-shell">
      <Header />
      <main className="homepage-main" data-homepage-sections={homepageSectionOrder.join(',')}>
        <Hero />
        <Problem />
        <HowItWorks />
        <BilingualAnalysis />
        <LiveActivityPreview />
        <ProductPreview />
        <Offers />
        <Trust />
        <Faq />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  );
}
