"use client";

import { motion } from "framer-motion";
import { siteConfig } from "../content/data";
import Link from "next/link";
import { LiveNetworkGraph } from "./LiveNetworkGraph";

export function Hero() {
  return (
    <section className="relative pt-40 pb-0 overflow-hidden bg-cantor-blue min-h-[85vh] flex flex-col justify-end">
      {/* Abstract Circuit Line overlay */}
      <div className="absolute inset-0 z-0 opacity-40">
        <div className="thin-line-path" style={{
          top: '20%',
          left: '10%',
          width: '70%',
          height: '40%',
          borderWidth: '1px 1px 0 0',
          borderTopRightRadius: '16px'
        }}></div>
        <div className="thin-line-path" style={{
          top: '20%',
          left: '80%',
          width: '15%',
          height: '60%',
          borderWidth: '0 1px 1px 0',
          borderBottomRightRadius: '16px'
        }}></div>
      </div>
      
      <div className="w-full px-6 relative z-10 flex-1 flex flex-col justify-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="pb-20 max-w-7xl mx-auto w-full"
        >
          <h1 className="text-7xl md:text-[100px] font-bold tracking-tighter text-white mb-24 text-balance leading-[1.0]">
            Enterprise Infrastructure<br/>for Sovereign Autonomy
          </h1>
          
          <div className="flex flex-col lg:flex-row justify-between items-end gap-12 w-full pr-12">
             {/* Left side: Live 3D Diagram */}
             <div className="relative w-full lg:w-1/2 h-[300px] md:h-[400px] opacity-80">
                <LiveNetworkGraph />
             </div>

             {/* Right side: Subtext and CTA */}
             <div className="max-w-xl w-full lg:w-1/2">
               <h2 className="text-3xl md:text-4xl font-medium text-white mb-6 text-balance leading-tight tracking-tight">
                 Unified orchestration, telemetry, and execution within a single configurable engine
               </h2>

               <p className="text-base text-white/90 mb-8 text-balance leading-relaxed font-light">
                 AetherGrid delivers a production-grade infrastructure layer for critical systems. Fusing live urban telemetry with conformal prediction and safety constraints into a single resilient platform designed for infinite scale.
               </p>
               
               <div className="inline-flex bg-white text-cantor-blue p-1 rounded-sm">
                 <Link
                   href={siteConfig.links.dashboard}
                   className="px-6 py-2 font-semibold hover:bg-slate-100 transition-colors bg-white text-cantor-blue text-sm flex items-center justify-between min-w-[200px]"
                 >
                   The Engine <span className="ml-4 font-bold">↗</span>
                 </Link>
               </div>
             </div>
          </div>
        </motion.div>
      </div>

    </section>
  );
}
