"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import ScenarioBuilder from "@/components/ScenarioBuilder";
import SafetyDashboard from "@/components/SafetyDashboard";
import { Activity, ShieldAlert, ShieldCheck } from "lucide-react";

// Dynamically import Map component to avoid SSR issues with maplibre/deck.gl
const DigitalTwinMap = dynamic(() => import("@/components/DigitalTwinMap"), {
  ssr: false,
  loading: () => <div className="map-loading glow-effect">Initializing AetherGrid Quantum Map...</div>,
});

export default function Home() {
  const [activeTab, setActiveTab] = useState<"scenario" | "safety">("scenario");
  const [certificate, setCertificate] = useState<any>(null);

  return (
    <main className="main-layout">
      {/* Background Map Layer */}
      <div className="map-container">
        <DigitalTwinMap certificate={certificate} />
      </div>

      {/* Floating Header */}
      <header className="glass-panel top-header">
        <div className="logo-section">
          <Activity size={24} color="var(--accent-primary)" />
          <h1>AetherGrid <span style={{ color: "var(--accent-secondary)" }}>Sovereign</span></h1>
        </div>
        <div className="status-indicators">
          <div className="status-pill safe">
            <ShieldCheck size={16} /> Certified Safe
          </div>
        </div>
      </header>

      {/* Left Sidebar Panel */}
      <aside className="glass-panel side-panel left-panel">
        <div className="panel-tabs">
          <button 
            className={`tab-btn ${activeTab === "scenario" ? "active" : ""}`}
            onClick={() => setActiveTab("scenario")}
          >
            Scenario Lab
          </button>
          <button 
            className={`tab-btn ${activeTab === "safety" ? "active" : ""}`}
            onClick={() => setActiveTab("safety")}
          >
            Safety & Diagnostics
          </button>
        </div>

        <div className="panel-content">
          {activeTab === "scenario" ? (
            <ScenarioBuilder 
              onSuccess={(cert: any) => {
                setCertificate(cert);
                setActiveTab("safety");
              }} 
            />
          ) : (
            <SafetyDashboard certificate={certificate} />
          )}
        </div>
      </aside>

      <style jsx>{`
        .main-layout {
          position: relative;
          width: 100vw;
          height: 100vh;
        }

        .map-container {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          z-index: 0;
        }

        .map-loading {
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-family: var(--font-mono);
          color: var(--accent-primary);
          background: var(--bg-dark);
        }

        .top-header {
          position: absolute;
          top: 1rem;
          left: 1rem;
          right: 1rem;
          height: 60px;
          z-index: 10;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 1.5rem;
        }

        .logo-section {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .logo-section h1 {
          font-size: 1.25rem;
          font-weight: 600;
          margin: 0;
          letter-spacing: 0.05em;
        }

        .status-pill {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.25rem 0.75rem;
          border-radius: 9999px;
          font-size: 0.75rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          border: 1px solid var(--success);
          color: var(--success);
          background: rgba(0, 230, 118, 0.1);
        }

        .side-panel {
          position: absolute;
          top: calc(1rem + 60px + 1rem);
          bottom: 1rem;
          width: 400px;
          z-index: 10;
          display: flex;
          flex-direction: column;
        }

        .left-panel {
          left: calc(70px + 2rem);
        }

        .panel-tabs {
          display: flex;
          border-bottom: 1px solid var(--border-color);
        }

        .tab-btn {
          flex: 1;
          background: transparent;
          border: none;
          padding: 1rem;
          color: var(--text-muted);
          font-family: var(--font-sans);
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
          border-bottom: 2px solid transparent;
        }

        .tab-btn:hover {
          color: var(--text-main);
          background: rgba(255, 255, 255, 0.02);
        }

        .tab-btn.active {
          color: var(--accent-primary);
          border-bottom-color: var(--accent-primary);
        }

        .panel-content {
          flex: 1;
          overflow-y: auto;
          padding: 1.5rem;
        }
      `}</style>
    </main>
  );
}
