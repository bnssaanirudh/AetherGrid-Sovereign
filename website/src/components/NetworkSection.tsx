"use client";

import { motion } from "framer-motion";
import { LiveNetworkGraph } from "./LiveNetworkGraph";
import Link from "next/link";
import { siteConfig } from "../content/data";
import { ArrowUpRight } from "lucide-react";

export function NetworkSection() {
  return (
    <section className="relative min-h-[90vh] bg-cantor-blue flex flex-col justify-center overflow-hidden border-t border-white/10">
      
      {/* Background Interactive Graph */}
      <div className="absolute inset-0 z-0">
        <div className="absolute inset-0 flex items-center justify-center">
           <div className="w-[120%] h-[120%] md:w-full md:h-full max-w-[1000px] max-h-[1000px]">
              <LiveNetworkGraph />
           </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 relative z-10 w-full pt-32 pb-12">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="max-w-3xl"
        >
          <h2 className="text-5xl md:text-7xl font-bold tracking-tighter text-white mb-8 text-balance leading-tight">
            Enterprise-Grade Infrastructure on AetherGrid
          </h2>
          
          <div className="inline-flex bg-white text-cantor-blue p-1 rounded-sm">
            <Link
              href={siteConfig.links.dashboard}
              className="px-6 py-2 font-semibold hover:bg-slate-100 transition-colors bg-white text-cantor-blue text-sm flex items-center justify-between min-w-[200px]"
            >
              Get in Touch <span className="ml-4 font-bold">↗</span>
            </Link>
          </div>
        </motion.div>
      </div>
      
      {/* Scroll Down Indicator */}
      <div className="absolute bottom-12 right-12 z-10 hidden md:block text-white/50 text-xs font-bold tracking-[0.2em]">
        SCROLL DOWN
      </div>
    </section>
  );
}
