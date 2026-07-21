import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { NewsroomSection } from "@/components/NewsroomSection";

export default function NewsPage() {
  return (
    <main className="min-h-screen">
      <Navbar />
      <div className="pt-24 bg-cantor-blue min-h-[50vh] flex items-center">
        <div className="max-w-7xl mx-auto px-6 py-20 w-full">
           <h1 className="text-6xl md:text-[90px] font-bold tracking-tighter text-white mb-6 leading-tight">
             Latest Announcements
           </h1>
           <p className="text-xl text-white/80 font-light max-w-3xl">
             Press releases, research updates, and major deployment announcements from the AetherGrid Sovereign team.
           </p>
        </div>
      </div>
      <NewsroomSection />
      <Footer />
    </main>
  );
}
