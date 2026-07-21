"use client";

import { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { capabilities } from "../content/data";
import { ArrowUpRight, Network, BrainCircuit, ListOrdered, Atom, ShieldCheck, Activity, LayoutDashboard, History } from "lucide-react";

const iconMap: Record<string, React.ElementType> = {
  Network,
  BrainCircuit,
  ListOrdered,
  Atom,
  ShieldCheck,
  Activity,
  LayoutDashboard,
  History
};

export function ScrollCarousel() {
  const targetRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: targetRef,
  });

  const x = useTransform(scrollYProgress, [0, 1], ["0%", "-65%"]);

  return (
    <section ref={targetRef} id="capabilities" className="relative h-[300vh] bg-[#0b0d10]">
      <div className="sticky top-0 h-screen flex items-center overflow-hidden">
        <div className="absolute top-24 left-6 md:left-24 z-10">
          <h2 className="text-sm font-semibold tracking-widest text-cyan-400 uppercase mb-3">
            Product Suite
          </h2>
          <h3 className="text-4xl md:text-6xl font-bold text-white tracking-tighter shadow-sm">
            Platform Capabilities
          </h3>
        </div>

        <motion.div style={{ x }} className="flex gap-8 px-6 md:px-24 mt-32">
          {capabilities.map((cap, i) => {
            const Icon = iconMap[cap.icon] || Network;
            return (
              <div
                key={i}
                className="group relative w-[350px] md:w-[450px] h-[500px] p-8 rounded-none bg-white/[0.02] border border-white/10 hover:bg-white/[0.04] hover:border-cyan-400/50 transition-all flex flex-col flex-shrink-0 backdrop-blur-md"
              >
                <div className="flex items-start justify-between mb-10">
                  <div className="w-14 h-14 bg-cyan-400/5 flex items-center justify-center border border-cyan-400/20 text-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.1)] group-hover:shadow-[0_0_25px_rgba(34,211,238,0.3)] transition-all">
                    <Icon className="w-7 h-7" />
                  </div>
                  {cap.research && (
                    <span className="text-[10px] font-semibold uppercase tracking-widest text-amber-400 border border-amber-400/30 px-3 py-1.5 bg-amber-400/5">
                      Research
                    </span>
                  )}
                </div>
                
                <h4 className="text-2xl font-bold text-white mb-4 group-hover:text-cyan-400 transition-colors tracking-tight">
                  {cap.title}
                </h4>
                <p className="text-base text-slate-400 mb-8 flex-grow leading-relaxed font-light">
                  {cap.description}
                </p>
                
                <div className="mt-auto flex items-center text-xs font-semibold tracking-[0.2em] text-slate-500 group-hover:text-cyan-400 transition-colors uppercase">
                  Explore Component <ArrowUpRight className="w-4 h-4 ml-2" />
                </div>
              </div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}
