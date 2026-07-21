"use client";

import { dependencies } from "../content/data";

export function LogoMarquee() {
  return (
    <section className="py-12 border-y border-white/5 bg-slate-900/30 overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 mb-8">
        <p className="text-xs font-semibold tracking-widest text-slate-500 uppercase">
          Built on Open-Source Infrastructure
        </p>
      </div>
      
      <div className="relative flex overflow-x-hidden group">
        <div className="animate-marquee whitespace-nowrap flex items-center gap-12 group-hover:[animation-play-state:paused]">
          {[...dependencies, ...dependencies, ...dependencies].map((dep, idx) => (
            <span
              key={idx}
              className="text-lg md:text-xl font-bold text-slate-600 hover:text-slate-300 transition-colors mx-4"
              aria-hidden={idx >= dependencies.length ? "true" : "false"}
            >
              {dep.name}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
