"use client";

import { motion } from "framer-motion";
import { ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { siteConfig } from "../content/data";

const products = [
  {
    tag: "TELEMETRY",
    title: "Live Grid Ingestion",
    desc: "Real-time streaming infrastructure providing massive-scale ingestion of urban telemetry data, IoT sensors, and latency-sensitive state changes.",
    className: "col-span-1 md:col-span-2 row-span-2 bg-cantor-blue",
  },
  {
    tag: "PREDICTION",
    title: "Conformal Engine",
    desc: "Statistical bounds computation engine that provides mathematically guaranteed confidence intervals for dynamic urban infrastructure loads.",
    className: "col-span-1 md:col-span-2 bg-cantor-blue",
  },
  {
    tag: "ORCHESTRATION",
    title: "Sovereign Watchdog",
    desc: "Automated safety policy enforcement layer ensuring all grid operations stay strictly within predefined operational phase bounds and safety thresholds.",
    className: "col-span-1 md:col-span-2 row-span-3 bg-cantor-blue",
  },
  {
    tag: "SIMULATION",
    title: "Scenario Lab",
    desc: "A pure digital twin environment allowing operators to run what-if simulations against live data without affecting the physical grid.",
    className: "col-span-1 md:col-span-2 bg-cantor-blue",
  },
  {
    tag: "TOPOLOGY",
    title: "Digital Twin Mapping",
    desc: "High-performance geospatial mapping layer utilizing WebGL to visualize millions of nodes, power flows, and infrastructure health in real-time.",
    className: "col-span-1 md:col-span-2 bg-cantor-blue",
  }
];

export function ProductSuite() {
  return (
    <section className="py-24 bg-cantor-black text-white">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex flex-col md:flex-row justify-between items-start mb-20 gap-12">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="flex-1"
          >
            <h2 className="text-6xl md:text-[90px] font-bold tracking-tighter leading-[0.9]">
              Engine<br/>Architecture
            </h2>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="flex-1 max-w-lg"
          >
            <p className="text-lg text-white/80 font-light mb-8 leading-relaxed">
              A complete suite of modular infrastructure layers built to orchestrate and safeguard massive urban grids. AetherGrid's architecture covers the end-to-end process of ingesting raw telemetry, predicting phase bounds, and enforcing rigorous safety protocols.
            </p>
            <Link href={siteConfig.links.dashboard} className="inline-flex items-center gap-3 px-6 py-3 bg-transparent border border-white/30 hover:bg-white hover:text-cantor-black transition-colors font-medium">
              Access Dashboard <ArrowUpRight className="w-5 h-5" />
            </Link>
          </motion.div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 auto-rows-[250px]">
          {products.map((product, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: idx * 0.1 }}
              className={`relative p-8 border border-white/10 group cursor-pointer overflow-hidden flex flex-col justify-end hover:border-white/30 transition-all ${product.className}`}
            >
              {/* Geometric pattern overlay placeholder */}
              <div className="absolute inset-0 opacity-20 pointer-events-none group-hover:scale-105 transition-transform duration-700">
                 <div className="absolute top-[20%] left-[20%] w-[60%] h-[60%] border border-white/40"></div>
                 <div className="absolute top-[30%] left-[30%] w-[40%] h-[40%] border border-white/60"></div>
                 <div className="absolute top-[50%] left-0 w-[30%] h-px bg-white/60"></div>
                 <div className="absolute top-0 left-[50%] w-px h-[30%] bg-white/60"></div>
              </div>

              {/* Tag */}
              <div className="absolute top-6 left-6 text-[10px] font-bold tracking-[0.2em] px-2 py-1 bg-white/10 text-white">
                {product.tag}
              </div>

              {/* Arrow Button */}
              <div className="absolute top-6 right-6 w-10 h-10 bg-white flex items-center justify-center group-hover:bg-cantor-light transition-colors">
                <ArrowUpRight className="w-5 h-5 text-cantor-blue" />
              </div>

              <div className="relative z-10">
                <h3 className="text-2xl font-bold mb-3">{product.title}</h3>
                <p className="text-sm text-white/80 font-light leading-relaxed">
                  {product.desc}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
