import Link from "next/link";
import { siteConfig } from "../content/data";
import { Hexagon } from "lucide-react";

export function Footer() {
  return (
    <footer className="py-12 border-t border-white/10 bg-slate-950">
      <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-8">
        
        <div className="md:col-span-1">
          <Link href="/" className="flex items-center gap-2 mb-4 opacity-80 hover:opacity-100 transition-opacity">
            <Hexagon className="w-5 h-5 text-cyan-400" />
            <span className="font-bold tracking-tight text-white">
              AetherGrid<span className="text-slate-400 font-normal">Sovereign</span>
            </span>
          </Link>
          <p className="text-xs text-slate-500">
            © {new Date().getFullYear()} AetherGrid Research. All rights reserved.
          </p>
        </div>

        <div>
          <h5 className="text-sm font-semibold text-white mb-4">Product</h5>
          <ul className="space-y-2 text-sm text-slate-400">
            <li><Link href="#architecture" className="hover:text-cyan-400 transition-colors">Architecture</Link></li>
            <li><Link href="#capabilities" className="hover:text-cyan-400 transition-colors">Capabilities</Link></li>
            <li><a href={siteConfig.links.dashboard} className="hover:text-cyan-400 transition-colors">Operator Dashboard</a></li>
          </ul>
        </div>

        <div>
          <h5 className="text-sm font-semibold text-white mb-4">Research</h5>
          <ul className="space-y-2 text-sm text-slate-400">
            <li><a href={`${siteConfig.links.github}/blob/main/docs/manuscript_asc.md`} className="hover:text-cyan-400 transition-colors">Manuscript</a></li>
            <li><a href={`${siteConfig.links.github}/blob/main/artifacts/performance_report.md`} className="hover:text-cyan-400 transition-colors">Benchmarks</a></li>
            <li><a href={`${siteConfig.links.github}/blob/main/docs/security/threat_model.md`} className="hover:text-cyan-400 transition-colors">Security Model</a></li>
          </ul>
        </div>

        <div>
          <h5 className="text-sm font-semibold text-white mb-4">Company</h5>
          <ul className="space-y-2 text-sm text-slate-400">
            <li><a href={siteConfig.links.github} className="hover:text-cyan-400 transition-colors">GitHub Repository</a></li>
            <li><a href={`${siteConfig.links.github}/blob/main/LICENSE`} className="hover:text-cyan-400 transition-colors">License</a></li>
          </ul>
        </div>
      </div>
    </footer>
  );
}
