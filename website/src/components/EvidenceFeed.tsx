"use client";

import { motion } from "framer-motion";
import { evidenceFeed, siteConfig } from "../content/data";
import { ArrowRight, FileText } from "lucide-react";
import Link from "next/link";

export function EvidenceFeed() {
  return (
    <section id="evidence" className="py-24 md:py-32">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-16 gap-6">
          <div>
            <h2 className="text-sm font-semibold tracking-widest text-cyan-400 uppercase mb-3">
              Research & Evidence
            </h2>
            <h3 className="text-3xl md:text-4xl font-bold text-white tracking-tight">
              Verifiable Artifacts
            </h3>
          </div>
          <a
            href={siteConfig.links.github}
            target="_blank"
            rel="noreferrer"
            className="text-sm font-medium text-slate-400 hover:text-white transition-colors flex items-center"
          >
            View all on GitHub <ArrowRight className="w-4 h-4 ml-2" />
          </a>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {evidenceFeed.map((item, i) => (
            <motion.a
              key={i}
              href={`${siteConfig.links.github}/blob/main/${item.link}`}
              target="_blank"
              rel="noreferrer"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.1 }}
              className="group block p-8 rounded-2xl bg-white/[0.02] border border-white/10 hover:bg-white/[0.04] hover:border-white/20 transition-all"
            >
              <div className="flex items-center justify-between mb-8">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  {item.type}
                </span>
                <span className="text-xs text-slate-600">{item.date}</span>
              </div>
              <FileText className="w-8 h-8 text-slate-400 group-hover:text-cyan-400 transition-colors mb-4" />
              <h4 className="text-xl font-bold text-white group-hover:text-cyan-400 transition-colors leading-snug">
                {item.title}
              </h4>
            </motion.a>
          ))}
        </div>
      </div>
    </section>
  );
}
