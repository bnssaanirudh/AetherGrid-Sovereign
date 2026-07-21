import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { CompanySection } from "@/components/CompanySection";
import Image from "next/image";

export default function CareerPage() {
  return (
    <main className="min-h-screen bg-cantor-black text-white">
      <Navbar />
      <div className="pt-24 min-h-[50vh] flex items-center border-b border-white/10 bg-cantor-blue">
        <div className="max-w-7xl mx-auto px-6 py-20 w-full grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
           <div>
               <h1 className="text-6xl md:text-[90px] font-bold tracking-tighter mb-6 leading-tight">
                 Join the<br/>Mission
               </h1>
               <p className="text-xl text-white/80 font-light max-w-lg">
                 We are always looking for world-class researchers and engineers to help us secure the future of autonomous infrastructure.
               </p>
           </div>
           <div className="relative aspect-video w-full">
              <Image src="/career_office.png" alt="Office" fill className="object-cover opacity-80" />
           </div>
        </div>
      </div>
      
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-4xl font-bold mb-12">Open Roles</h2>
          
          <div className="space-y-4">
             {["Distributed Systems Engineer (Rust)", "Quantum ML Researcher", "Senior Frontend Engineer (WebGL)", "Infrastructure Architect"].map((role, idx) => (
                <div key={idx} className="flex justify-between items-center p-8 border border-white/10 hover:border-white/30 hover:bg-white/5 transition-all cursor-pointer group">
                   <h3 className="text-2xl font-semibold group-hover:text-cantor-blue transition-colors">{role}</h3>
                   <span className="text-white/60">New York / Remote</span>
                </div>
             ))}
          </div>
        </div>
      </section>
      
      <Footer />
    </main>
  );
}
