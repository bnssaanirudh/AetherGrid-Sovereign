import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { CompanySection } from "@/components/CompanySection";

export default function CompanyPage() {
  return (
    <main className="min-h-screen">
      <Navbar />
      <div className="pt-24 bg-cantor-blue min-h-[50vh] flex items-center border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-20 w-full">
           <h1 className="text-6xl md:text-[90px] font-bold tracking-tighter text-white mb-6 leading-tight">
             Securing the<br/>Next Generation<br/>of Grids
           </h1>
           <p className="text-xl text-white/80 font-light max-w-3xl">
             AetherGrid Sovereign was founded on a simple principle: autonomous infrastructure requires mathematically guaranteed safety bounds. We are building the foundational orchestration layer for critical systems worldwide.
           </p>
        </div>
      </div>
      <CompanySection />
      <Footer />
    </main>
  );
}
