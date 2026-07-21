"use client";

import { motion } from "framer-motion";
import { siteConfig } from "../content/data";

export function SplitSection() {
  return (
    <section id="architecture" className="py-32 md:py-48 bg-[#0b0d10] overflow-hidden">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
          
          {/* Left Copy */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-xs font-semibold tracking-[0.2em] text-cyan-400 uppercase mb-6">
              Foundation
            </h2>
            <h3 className="text-4xl md:text-5xl font-bold text-white tracking-tighter mb-8 text-balance leading-tight">
              Why AetherGrid matters for modern city infrastructure.
            </h3>
            <div className="space-y-6 text-slate-400 text-lg font-light leading-relaxed">
              <p>
                Urban environments rely on deeply coupled physical networks—power grids, transit arteries, and emergency response routes. When one node fails under extreme weather, the cascade traverses structural boundaries unpredictably.
              </p>
              <p>
                AetherGrid Sovereign replaces static rule-based thresholds with a heterogeneous graph neural network architecture. By fusing real-time IoT telemetry with predictive hazard models, operators can visualize and isolate topological vulnerabilities hours before physical failure occurs.
              </p>
            </div>
            
            <div className="mt-10">
              <a 
                href={siteConfig.links.github} 
                target="_blank"
                rel="noreferrer"
                className="text-cyan-400 font-semibold hover:text-cyan-300 transition-colors inline-flex items-center"
              >
                Read the Architecture Documentation
                <svg className="w-4 h-4 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </a>
            </div>
          </motion.div>
          
          {/* Right Abstract Visual */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="relative h-[400px] w-full rounded-2xl border border-white/10 bg-slate-950 overflow-hidden flex items-center justify-center shadow-2xl shadow-cyan-900/20"
          >
            {/* Abstract node/edge visualization using CSS */}
            <div className="absolute inset-0 opacity-30 bg-[linear-gradient(to_right,#22d3ee12_1px,transparent_1px),linear-gradient(to_bottom,#22d3ee12_1px,transparent_1px)] bg-[size:40px_40px]" />
            <div className="relative z-10 grid grid-cols-3 gap-8">
              {[...Array(9)].map((_, i) => (
                <div key={i} className={`w-3 h-3 rounded-full ${i === 4 ? 'bg-amber-400 animate-pulse shadow-[0_0_15px_rgba(251,191,36,0.8)]' : 'bg-cyan-500/50 shadow-[0_0_10px_rgba(34,211,238,0.5)]'}`} />
              ))}
            </div>
            <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent pointer-events-none" />
          </motion.div>

        </div>
      </div>
    </section>
  );
}
