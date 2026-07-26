"use client";

import React from 'react';
import { Database, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function DataQualityPage() {
  return (
    <main className="page-container">
      <header className="glass-panel header">
        <Database size={24} color="var(--accent-primary)" />
        <h1>Data Quality & Ingestion</h1>
      </header>

      <div className="content-grid">
        <div className="glass-panel metric-box">
          <div className="label">Live Sensors</div>
          <div className="value">14,230</div>
          <div className="sub-text" style={{ color: 'var(--success)' }}><ShieldCheck size={14}/> 99.8% Online</div>
        </div>
        
        <div className="glass-panel metric-box">
          <div className="label">Quarantined Records</div>
          <div className="value">42</div>
          <div className="sub-text" style={{ color: 'var(--warning)' }}><AlertTriangle size={14}/> Requires review</div>
        </div>
        
        <div className="glass-panel metric-box">
          <div className="label">Data Freshness</div>
          <div className="value">3.2s</div>
          <div className="sub-text" style={{ color: 'var(--success)' }}>Optimal</div>
        </div>
      </div>

      <div className="glass-panel logs-panel">
        <h3>Recent Ingestion Logs</h3>
        <div className="log-list">
          <div className="log-item">
            <span className="time">10:32:45</span>
            <span className="source">[OSM-Stream]</span>
            <span className="msg">Synchronized 12 new road segment statuses.</span>
          </div>
          <div className="log-item">
            <span className="time">10:32:40</span>
            <span className="source">[WeatherBench]</span>
            <span className="msg">Ingested temperature map update (Chicago).</span>
          </div>
          <div className="log-item warning">
            <span className="time">10:32:38</span>
            <span className="source">[PowerGrid-IoT]</span>
            <span className="msg">Dropped 3 packets from substation N-42 (stale data).</span>
          </div>
        </div>
      </div>

      <style jsx>{`
        .page-container {
          padding: 2rem;
          padding-left: calc(70px + 2rem); /* Account for sidebar */
          display: flex;
          flex-direction: column;
          gap: 2rem;
          min-height: 100vh;
        }

        .header {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 1.5rem;
        }

        .header h1 {
          font-size: 1.5rem;
          font-weight: 600;
        }

        .content-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 1.5rem;
        }

        .metric-box {
          padding: 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .label {
          color: var(--text-muted);
          text-transform: uppercase;
          font-size: 0.75rem;
          letter-spacing: 0.05em;
        }

        .value {
          font-size: 2.5rem;
          font-weight: 700;
          color: var(--text-main);
        }

        .sub-text {
          display: flex;
          align-items: center;
          gap: 0.25rem;
          font-size: 0.875rem;
        }

        .logs-panel {
          padding: 1.5rem;
          flex: 1;
        }

        .logs-panel h3 {
          margin-bottom: 1rem;
          font-size: 1.125rem;
        }

        .log-list {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
          font-family: var(--font-mono);
          font-size: 0.875rem;
        }

        .log-item {
          display: flex;
          gap: 1rem;
          padding: 0.5rem;
          border-bottom: 1px solid rgba(255,255,255,0.05);
        }

        .log-item.warning {
          color: var(--warning);
        }

        .time {
          color: var(--text-muted);
        }

        .source {
          color: var(--accent-primary);
        }
      `}</style>
    </main>
  );
}
