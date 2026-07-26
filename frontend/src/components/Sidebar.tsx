"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Activity, Database, FlaskConical, LayoutDashboard } from 'lucide-react';

export default function Sidebar() {
  const pathname = usePathname();

  const links = [
    { href: '/', label: 'Live Twin', icon: LayoutDashboard },
    { href: '/data', label: 'Data Quality', icon: Database },
    { href: '/research', label: 'Research Lab', icon: FlaskConical },
  ];

  return (
    <nav className="glass-panel sidebar-nav">
      <div className="sidebar-logo">
        <Activity size={28} color="var(--accent-primary)" className="glow-effect" />
      </div>
      
      <div className="nav-links">
        {links.map((link) => {
          const Icon = link.icon;
          const isActive = pathname === link.href;
          
          return (
            <Link 
              key={link.href} 
              href={link.href}
              className={`nav-link ${isActive ? 'active' : ''}`}
              title={link.label}
            >
              <Icon size={22} />
            </Link>
          );
        })}
      </div>

      <style jsx>{`
        .sidebar-nav {
          position: fixed;
          top: 1rem;
          bottom: 1rem;
          left: 1rem;
          width: 70px;
          z-index: 100;
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 1.5rem 0;
          gap: 2rem;
        }

        .nav-links {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
          width: 100%;
        }

        .nav-link {
          display: flex;
          justify-content: center;
          align-items: center;
          width: 100%;
          height: 40px;
          color: var(--text-muted);
          transition: all 0.3s ease;
          border-left: 3px solid transparent;
        }

        .nav-link:hover {
          color: var(--text-main);
          background: rgba(255, 255, 255, 0.05);
        }

        .nav-link.active {
          color: var(--accent-primary);
          border-left-color: var(--accent-primary);
          background: var(--accent-primary-dim);
        }
      `}</style>
    </nav>
  );
}
