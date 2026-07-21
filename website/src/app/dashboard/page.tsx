"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import ScenarioBuilder from "@/components/dashboard/ScenarioBuilder";
import SafetyDashboard from "@/components/dashboard/SafetyDashboard";
import { Activity, ShieldCheck, ChevronUp, ChevronDown, TerminalSquare } from "lucide-react";
import Link from "next/link";

// Dynamically import Map component to avoid SSR issues with maplibre/deck.gl
const DigitalTwinMap = dynamic(() => import("@/components/dashboard/DigitalTwinMap"), {
  ssr: false,
  loading: () => <div className="map-loading bg-cantor-blue text-white flex items-center justify-center h-full w-full font-mono">Initializing AetherGrid Map...</div>,
});

export default function Home() {
  const [activeTab, setActiveTab] = useState<"scenario" | "safety">("scenario");
  const [panelOpen, setPanelOpen] = useState(true);

  return (
    <main className="main-layout bg-cantor-black">
      {/* Background Map Layer */}
      <div className="map-container absolute inset-0 z-0">
        <DigitalTwinMap />
      </div>

      {/* Floating Header (Cantor8 Style Minimalist) */}
      <header className="absolute top-0 left-0 right-0 h-16 z-10 flex items-center justify-between px-6 bg-cantor-black/80 backdrop-blur-md border-b border-white/10">
        <div className="flex items-center gap-4">
          <Link href="/" className="flex items-center gap-2 group">
             <div className="grid grid-cols-2 gap-[2px]">
               <div className="w-2 h-2 bg-white/70"></div>
               <div className="w-2 h-2 bg-white"></div>
               <div className="w-2 h-2 bg-white"></div>
               <div className="w-2 h-2 bg-cantor-light"></div>
            </div>
            <span className="font-bold tracking-widest text-lg text-white uppercase ml-2">
              AetherGrid <span className="text-white/50 font-normal">Operator</span>
            </span>
          </Link>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1 rounded bg-white/5 border border-white/10 text-xs font-semibold text-white tracking-widest uppercase">
            <ShieldCheck size={14} className="text-cantor-light" /> Certified Safe
          </div>
        </div>
      </header>

      {/* Sleek Floating Command Palette (Bottom Right) */}
      <div className={`absolute bottom-6 right-6 w-96 bg-cantor-black border border-white/20 shadow-2xl z-20 flex flex-col transition-all duration-300 ${panelOpen ? 'h-[500px]' : 'h-12'}`}>
         
         {/* Palette Header */}
         <div 
            className="h-12 border-b border-white/10 flex items-center justify-between px-4 bg-white/5 cursor-pointer hover:bg-white/10 transition-colors"
            onClick={() => setPanelOpen(!panelOpen)}
         >
            <div className="flex items-center gap-2 text-white font-medium text-sm tracking-wide">
               <TerminalSquare size={16} className="text-cantor-light" />
               COMMAND CONSOLE
            </div>
            <button className="text-white/70 hover:text-white">
               {panelOpen ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
            </button>
         </div>

         {/* Palette Content */}
         {panelOpen && (
            <div className="flex flex-col flex-1 overflow-hidden">
               <div className="flex border-b border-white/10">
                  <button 
                     className={`flex-1 py-3 text-xs font-semibold tracking-wider uppercase transition-colors ${activeTab === "scenario" ? "bg-cantor-blue text-white" : "text-white/50 hover:bg-white/5 hover:text-white"}`}
                     onClick={() => setActiveTab("scenario")}
                  >
                     Scenario Lab
                  </button>
                  <button 
                     className={`flex-1 py-3 text-xs font-semibold tracking-wider uppercase transition-colors ${activeTab === "safety" ? "bg-cantor-blue text-white" : "text-white/50 hover:bg-white/5 hover:text-white"}`}
                     onClick={() => setActiveTab("safety")}
                  >
                     Safety & Diagnostics
                  </button>
               </div>
               
               <div className="flex-1 overflow-y-auto p-4 custom-scrollbar bg-cantor-black">
                  {activeTab === "scenario" ? <ScenarioBuilder /> : <SafetyDashboard />}
               </div>
            </div>
         )}
      </div>

      <style jsx>{`
        .main-layout {
          position: relative;
          width: 100vw;
          height: 100vh;
          overflow: hidden;
        }
        
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.2);
        }
      `}</style>
    </main>
  );
}
