"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useCases } from "../content/data";
import { TerminalSquare, ChevronRight } from "lucide-react";

export function UseCaseTabs() {
  const [activeTab, setActiveTab] = useState(useCases[0].id);

  return (
    <section className="py-24 md:py-40 border-y border-white/5 bg-[#0b0d10] relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-cyan-900/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="max-w-7xl mx-auto px-6 relative z-10">
        <div className="mb-20">
          <h2 className="text-sm font-semibold tracking-widest text-cyan-400 uppercase mb-4">
            Interactive Terminal
          </h2>
          <h3 className="text-4xl md:text-5xl font-bold text-white tracking-tighter">
            Architected for Resilience.
          </h3>
        </div>

        <div className="flex flex-col lg:flex-row gap-16">
          {/* Left Column: Terminal Tabs */}
          <div className="lg:w-1/3 flex flex-col gap-2">
            {useCases.map((useCase) => (
              <button
                key={useCase.id}
                onClick={() => setActiveTab(useCase.id)}
                className={`text-left px-6 py-5 rounded-none border-l-2 transition-all flex items-center justify-between group ${
                  activeTab === useCase.id
                    ? "bg-white/[0.03] border-cyan-400 text-white"
                    : "border-transparent text-slate-500 hover:text-slate-300 hover:bg-white/[0.01]"
                }`}
                role="tab"
                aria-selected={activeTab === useCase.id}
              >
                <span className="font-mono text-sm tracking-wide">{useCase.label}</span>
                <ChevronRight className={`w-4 h-4 transition-transform ${activeTab === useCase.id ? "text-cyan-400 translate-x-1" : "opacity-0 group-hover:opacity-100"}`} />
              </button>
            ))}
          </div>

          {/* Right Column: Glassmorphic Panel */}
          <div className="lg:w-2/3 min-h-[450px] relative">
            <div className="absolute inset-0 bg-white/[0.02] backdrop-blur-xl border border-white/10 shadow-2xl p-1 shadow-cyan-900/10">
              {/* Fake Terminal Header */}
              <div className="h-10 bg-black/40 border-b border-white/10 flex items-center px-4 gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-slate-700" />
                <div className="w-2.5 h-2.5 rounded-full bg-slate-700" />
                <div className="w-2.5 h-2.5 rounded-full bg-slate-700" />
                <div className="ml-auto font-mono text-[10px] text-slate-500 tracking-widest">
                  bash: aethergrid-cli
                </div>
              </div>
              
              {/* Content Area */}
              <div className="p-8 md:p-12 relative overflow-hidden h-[calc(100%-40px)] flex flex-col justify-center">
                <AnimatePresence mode="wait">
                  {useCases.map((useCase) => (
                    useCase.id === activeTab && (
                      <motion.div
                        key={useCase.id}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        transition={{ duration: 0.4 }}
                        role="tabpanel"
                        className="relative z-10"
                      >
                        <TerminalSquare className="w-10 h-10 text-cyan-400 mb-8 opacity-80" />
                        <h4 className="text-3xl font-bold text-white mb-6 tracking-tight leading-tight max-w-lg">
                          {useCase.title}
                        </h4>
                        <p className="text-lg text-slate-400 leading-relaxed font-light text-balance max-w-xl">
                          {useCase.description}
                        </p>
                        
                        {/* Fake terminal execution log */}
                        <div className="mt-12 pt-8 border-t border-white/10 font-mono text-xs text-slate-500">
                          <span className="text-cyan-400">~</span> aethergrid exec --module {useCase.id} <br/>
                          [OK] Connecting to sovereign mesh...<br/>
                          [OK] Validating node state hashes...<br/>
                          [OK] Simulation complete.
                        </div>
                      </motion.div>
                    )
                  ))}
                </AnimatePresence>
                
                {/* Background terminal asset placeholder */}
                <div className="absolute right-[-100px] bottom-[-100px] w-[400px] h-[400px] opacity-10 pointer-events-none">
                  {/* The user will inject the UI mockup PNG here */}
                  <div className="w-full h-full border border-cyan-400/50 rounded-full bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-cyan-400/20 to-transparent" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
