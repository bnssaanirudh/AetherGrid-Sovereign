"use client";

import React from 'react';
import { FlaskConical } from 'lucide-react';

export default function ResearchPage() {
  return (
    <main className="page-container">
      <header className="glass-panel header">
        <FlaskConical size={24} color="var(--accent-secondary)" />
        <h1>Research Lab & Model Comparison</h1>
      </header>

      <div className="glass-panel content-area">
        <h2>Offline Experiments</h2>
        <p className="text-muted">Compare HGT (Quantum-Fuzzy) vs baseline CV-PFA MLP models.</p>
        
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Model</th>
                <th>Phase Error</th>
                <th>Calibration (ECE)</th>
                <th>Bound Coverage</th>
                <th>Inference (ms)</th>
              </tr>
            </thead>
            <tbody>
              <tr className="highlight">
                <td>AetherGrid-Q-HGT</td>
                <td>1.0%</td>
                <td>0.160</td>
                <td>99.0%</td>
                <td>45</td>
              </tr>
              <tr>
                <td>CV-PFA MLP</td>
                <td>N/A</td>
                <td>0.277</td>
                <td>84.5%</td>
                <td>12</td>
              </tr>
              <tr>
                <td>GCN-Baseline</td>
                <td>8.5%</td>
                <td>0.220</td>
                <td>91.2%</td>
                <td>28</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <style jsx>{`
        .page-container {
          padding: 2rem;
          padding-left: calc(70px + 2rem);
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

        .content-area {
          padding: 2rem;
          flex: 1;
        }

        .content-area h2 {
          margin-bottom: 0.5rem;
        }

        .text-muted {
          color: var(--text-muted);
          margin-bottom: 2rem;
        }

        .table-container {
          overflow-x: auto;
        }

        .data-table {
          width: 100%;
          border-collapse: collapse;
          text-align: left;
        }

        .data-table th {
          padding: 1rem;
          border-bottom: 2px solid var(--border-color);
          color: var(--text-muted);
          font-weight: 500;
        }

        .data-table td {
          padding: 1rem;
          border-bottom: 1px solid rgba(255,255,255,0.05);
        }

        .data-table tr.highlight {
          background: var(--accent-primary-dim);
          border-left: 2px solid var(--accent-primary);
        }
      `}</style>
    </main>
  );
}
