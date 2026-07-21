"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import Image from "next/image";
import { ArrowUpRight } from "lucide-react";

export function NewsroomSection() {
  const articles = [
    {
      type: "Research",
      date: "7.21.2026",
      title: "Conformal Engine Achieves 99.9% Abstention Accuracy on NYC Grid Data",
      image: "/news_abstract_1.png",
      link: "/news"
    },
    {
      type: "Partnership",
      date: "7.15.2026",
      title: "AetherGrid Deploys Sovereign Watchdog Across Tier-1 Utility Providers",
      image: "/news_abstract_2.png",
      link: "/news"
    }
  ];

  return (
    <section className="py-24 bg-white text-cantor-blue">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex justify-between items-end mb-16">
          <h2 className="text-5xl md:text-7xl font-bold tracking-tighter">
            Newsroom
          </h2>
          <Link href="/news" className="hidden md:flex items-center gap-2 font-semibold hover:opacity-70 transition-opacity">
             View all <ArrowUpRight className="w-5 h-5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {articles.map((article, idx) => (
            <Link href={article.link} key={idx} className="group block">
              <div className="relative w-full aspect-[4/3] bg-cantor-black mb-6 overflow-hidden">
                 <Image 
                   src={article.image}
                   alt={article.title}
                   fill
                   className="object-cover group-hover:scale-105 transition-transform duration-700"
                 />
              </div>
              <div className="flex items-center gap-4 text-sm font-bold tracking-wider mb-3">
                 <span className="px-2 py-1 border border-cantor-blue/20">{article.type}</span>
                 <span className="text-cantor-blue/60">{article.date}</span>
              </div>
              <h3 className="text-2xl md:text-3xl font-bold leading-tight group-hover:text-cantor-blue/80 transition-colors">
                {article.title}
              </h3>
            </Link>
          ))}
        </div>
        
        <div className="mt-8 md:hidden">
          <Link href="/news" className="flex items-center gap-2 font-semibold hover:opacity-70 transition-opacity">
             View all <ArrowUpRight className="w-5 h-5" />
          </Link>
        </div>
      </div>
    </section>
  );
}
