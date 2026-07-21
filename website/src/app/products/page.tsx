import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { ProductSuite } from "@/components/ProductSuite";
import { NetworkSection } from "@/components/NetworkSection";

export default function ProductsPage() {
  return (
    <main className="min-h-screen">
      <Navbar />
      <div className="pt-24 bg-cantor-black min-h-[50vh] flex items-center">
        <div className="max-w-7xl mx-auto px-6 py-20 w-full">
           <h1 className="text-6xl md:text-[90px] font-bold tracking-tighter text-white mb-6 leading-tight">
             Engine Architecture
           </h1>
           <p className="text-xl text-white/80 font-light max-w-3xl">
             Deep dive into the AetherGrid Sovereign infrastructure suite. From raw telemetry ingestion to mathematically guaranteed safety bounds.
           </p>
        </div>
      </div>
      <ProductSuite />
      <NetworkSection />
      <Footer />
    </main>
  );
}
