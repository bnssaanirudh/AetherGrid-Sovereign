"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import Image from "next/image";
import { ArrowUpRight } from "lucide-react";

export function CompanySection() {
  return (
    <section className="py-24 bg-cantor-blue text-white overflow-hidden border-t border-white/10">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="text-5xl md:text-7xl font-bold tracking-tighter mb-8 leading-[1.0]">
              Built for<br/>Real-World<br/>Resilience
            </h2>
            <p className="text-lg md:text-xl text-white/80 font-light leading-relaxed mb-10 max-w-lg">
              Our team consists of world-class researchers and engineers from distributed systems, quantum machine learning, and critical infrastructure domains. We are scaling AetherGrid Sovereign to secure the next generation of automated urban networks.
            </p>
            
            <div className="flex gap-4">
               <Link href="/company" className="inline-flex items-center gap-2 px-6 py-3 bg-white text-cantor-blue font-semibold hover:bg-slate-100 transition-colors">
                  Our Company <ArrowUpRight className="w-4 h-4" />
               </Link>
               <Link href="/career" className="inline-flex items-center gap-2 px-6 py-3 border border-white/30 text-white font-semibold hover:bg-white/10 transition-colors">
                  Join the Team
               </Link>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="relative w-full aspect-[4/3] bg-cantor-black border border-white/10"
          >
             <Image 
               src="/career_office.png"
               alt="AetherGrid Engineering Team"
               fill
               className="object-cover opacity-80"
             />
          </motion.div>

        </div>
      </div>
    </section>
  );
}
