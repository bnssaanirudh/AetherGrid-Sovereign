import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import Image from "next/image";

export default function BlogPage() {
  return (
    <main className="min-h-screen bg-cantor-black text-white">
      <Navbar />
      <div className="pt-24 min-h-[50vh] flex items-center border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-20 w-full">
           <h1 className="text-6xl md:text-[90px] font-bold tracking-tighter mb-6 leading-tight">
             Engineering Blog
           </h1>
           <p className="text-xl text-white/80 font-light max-w-3xl">
             Technical deep-dives into distributed systems, conformal prediction, and quantum machine learning.
           </p>
        </div>
      </div>
      
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
             <div className="group cursor-pointer">
                <div className="relative w-full aspect-video bg-cantor-blue mb-6 overflow-hidden">
                   <Image src="/news_abstract_1.png" alt="Blog 1" fill className="object-cover group-hover:scale-105 transition-transform duration-700" />
                </div>
                <h3 className="text-3xl font-bold mb-4">Implementing Conformal Prediction in Rust</h3>
                <p className="text-white/70">A deep dive into how we achieved microsecond latency for our safety bound calculations...</p>
             </div>
             
             <div className="group cursor-pointer">
                <div className="relative w-full aspect-video bg-cantor-blue mb-6 overflow-hidden">
                   <Image src="/news_abstract_2.png" alt="Blog 2" fill className="object-cover group-hover:scale-105 transition-transform duration-700" />
                </div>
                <h3 className="text-3xl font-bold mb-4">Scaling Live Network Telemetry</h3>
                <p className="text-white/70">Our architecture for ingesting and processing millions of IoT sensor events simultaneously...</p>
             </div>
          </div>
        </div>
      </section>
      
      <Footer />
    </main>
  );
}
