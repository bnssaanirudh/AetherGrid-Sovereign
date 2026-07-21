"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { siteConfig } from "../content/data";
import { Menu, X, ArrowUpRight } from "lucide-react";

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <nav
      className={`fixed top-0 w-full z-50 transition-all duration-300 border-b ${
        scrolled
          ? "bg-cantor-blue/95 backdrop-blur-md border-white/10 py-0"
          : "bg-cantor-blue border-transparent py-0"
      }`}
    >
      <div className="w-full px-6 flex items-stretch justify-between h-16">
        <div className="flex items-center">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="grid grid-cols-2 gap-[2px]">
               <div className="w-2 h-2 bg-white/70"></div>
               <div className="w-2 h-2 bg-white"></div>
               <div className="w-2 h-2 bg-white"></div>
               <div className="w-2 h-2 bg-cantor-light"></div>
            </div>
            <span className="font-bold tracking-widest text-lg text-white uppercase ml-2">
              AetherGrid
            </span>
          </Link>
        </div>

        {/* Desktop Nav - Middle */}
        <div className="hidden md:flex items-stretch text-sm font-medium text-white/90">
          <Link href="/" className="flex items-center px-6 bg-white text-cantor-blue">Home</Link>
          <Link href="#architecture" className="flex items-center px-6 hover:bg-white/10 transition-colors">Products</Link>
          <Link href="#capabilities" className="flex items-center px-6 hover:bg-white/10 transition-colors">Partners</Link>
          <Link href="#evidence" className="flex items-center px-6 hover:bg-white/10 transition-colors">News</Link>
          <a href={siteConfig.links.github} className="flex items-center px-6 hover:bg-white/10 transition-colors">Blog</a>
        </div>

        {/* Desktop Nav - Right */}
        <div className="hidden md:flex items-stretch text-sm font-medium text-white/90">
          <Link href="#career" className="flex items-center px-4 hover:bg-white/10 transition-colors">Career</Link>
          <Link href="#company" className="flex items-center px-4 hover:bg-white/10 transition-colors">Company</Link>
          <div className="flex items-center pl-4 py-2">
            <Link
              href={siteConfig.links.dashboard}
              className="flex items-center h-full bg-white text-cantor-blue transition-all"
            >
              <span className="px-5 font-semibold">Get in Touch</span>
              <div className="h-full px-3 bg-cantor-blue border-l-2 border-white flex items-center justify-center">
                 <ArrowUpRight className="w-4 h-4 text-white" />
              </div>
            </Link>
          </div>
        </div>

        {/* Mobile Toggle */}
        <div className="flex items-center md:hidden">
          <button className="text-white" onClick={() => setMobileOpen(!mobileOpen)}>
            {mobileOpen ? <X /> : <Menu />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileOpen && (
        <div className="md:hidden absolute top-full left-0 w-full bg-cantor-blue border-b border-white/10 px-6 py-4 flex flex-col gap-4 shadow-xl">
          <Link href="/" onClick={() => setMobileOpen(false)} className="text-white bg-white/20 px-4 py-2 rounded">Home</Link>
          <Link href="#architecture" onClick={() => setMobileOpen(false)} className="text-white/80 hover:text-white px-4">Products</Link>
          <Link href="#capabilities" onClick={() => setMobileOpen(false)} className="text-white/80 hover:text-white px-4">Partners</Link>
          <Link href={siteConfig.links.dashboard} className="text-white font-medium bg-white/10 px-4 py-2 mt-4 flex items-center justify-between">
            Get in Touch <ArrowUpRight className="w-4 h-4" />
          </Link>
        </div>
      )}
    </nav>
  );
}
