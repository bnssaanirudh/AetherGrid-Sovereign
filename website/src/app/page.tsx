import { Navbar } from "@/components/Navbar";
import { Hero } from "@/components/Hero";
import { TransitionBlueToBlack } from "@/components/TransitionBlueToBlack";
import { ProductSuite } from "@/components/ProductSuite";
import { NetworkSection } from "@/components/NetworkSection";
import { NewsroomSection } from "@/components/NewsroomSection";
import { CompanySection } from "@/components/CompanySection";
import { Footer } from "@/components/Footer";

export default function Home() {
  return (
    <main className="min-h-screen selection:bg-cyan-400/30">
      <Navbar />
      <Hero />
      <TransitionBlueToBlack />
      <ProductSuite />
      <NetworkSection />
      <NewsroomSection />
      <CompanySection />
      <Footer />
    </main>
  );
}
