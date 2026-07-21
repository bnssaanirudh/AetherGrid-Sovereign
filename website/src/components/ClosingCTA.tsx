"use client";

import { motion } from "framer-motion";
import { siteConfig } from "../content/data";
import { ArrowRight } from "lucide-react";

export function ClosingCTA() {
  return (
    <section className="py-24 border-y border-white/5 bg-slate-900/30 overflow-hidden relative">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-cyan-950/10 to-transparent" />
      
      <div className="max-w-4xl mx-auto px-6 text-center relative z-10">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="text-3xl md:text-5xl font-bold text-white tracking-tight mb-6">
            Predict the cascade before it happens.
          </h2>
          <p className="text-lg text-slate-400 mb-10 max-w-2xl mx-auto text-balance">
            Deploy the AetherGrid Sovereign Digital Twin to protect your city's most critical infrastructure with verifiable, mathematically bound guarantees.
          </p>
          <a
            href={siteConfig.links.dashboard}
            className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-md bg-white text-slate-950 font-bold hover:bg-slate-200 transition-colors"
          >
            Access the Dashboard
            <ArrowRight className="w-5 h-5" />
          </a>
        </motion.div>
      </div>

      {/* Pipeline Ticker */}
      <div className="mt-20 overflow-hidden opacity-50 select-none flex">
        <div className="animate-marquee whitespace-nowrap flex items-center gap-8 group-hover:[animation-play-state:paused]">
          {[...Array(4)].map((_, i) => (
            <span key={i} className="text-sm font-mono text-cyan-400/60 uppercase tracking-widest flex items-center gap-8 mx-4">
              <span>Ingestion</span> <ArrowRight className="w-4 h-4" />
              <span>Graph Snapshot</span> <ArrowRight className="w-4 h-4" />
              <span>CV-PFA Inference</span> <ArrowRight className="w-4 h-4" />
              <span>Calibration</span> <ArrowRight className="w-4 h-4" />
              <span>Certificate</span> <ArrowRight className="w-4 h-4" />
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
