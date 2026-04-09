import Header from '@/components/homepage/header';
import Hero from '@/components/homepage/hero';
import Problem from '@/components/homepage/problem';
import Offers from '@/components/homepage/offers';
import ProductPreview from '@/components/homepage/product-preview';
import HowItWorks from '@/components/homepage/how-it-works';
import SmeEnterprise from '@/components/homepage/sme-enterprise';
import Trust from '@/components/homepage/trust';
import FAQ from '@/components/homepage/faq';
import FinalCTA from '@/components/homepage/final-cta';
import Footer from '@/components/homepage/footer';

export default function HomePage() {
  return (
    <div className="relative">
      <Header />
      <Hero />
      <Problem />
      <Offers />
      <ProductPreview />
      <HowItWorks />
      <SmeEnterprise />
      <Trust />
      <FAQ />
      <FinalCTA />
      <Footer />
    </div>
  );
}
