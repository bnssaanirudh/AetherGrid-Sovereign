"use client";

import React from 'react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';
import { ShieldCheck, ShieldAlert, FileText, Download } from 'lucide-react';

const mockConfidenceData = [
  { name: '0s', hgt: 98, cv_pfa: 85 },
  { name: '10s', hgt: 95, cv_pfa: 80 },
  { name: '20s', hgt: 92, cv_pfa: 70 },
  { name: '30s', hgt: 88, cv_pfa: 55 },
  { name: '40s', hgt: 85, cv_pfa: 40 },
  { name: '50s', hgt: 82, cv_pfa: 25 },
];

const mockPhaseData = [
  { subject: 'Topology', A: 120, B: 110, fullMark: 150 },
  { subject: 'Sensor', A: 98, B: 130, fullMark: 150 },
  { subject: 'Hesitation', A: 86, B: 130, fullMark: 150 },
  { subject: 'Conformal', A: 99, B: 100, fullMark: 150 },
  { subject: 'Bound', A: 85, B: 90, fullMark: 150 },
  { subject: 'Calib', A: 65, B: 85, fullMark: 150 },
];

export default function SafetyDashboard() {
  return (
    <div className="safety-dashboard">
      <div className="cert-header">
        <ShieldCheck size={28} color="var(--success)" />
        <div>
          <h2>Prediction Certificate</h2>
          <p className="text-muted">ID: cert_success_01 • 99% Coverage</p>
        </div>
      </div>

      <div className="metric-cards">
        <div className="card">
          <div className="card-label">Bound Mode</div>
          <div className="card-value">Analytic</div>
        </div>
        <div className="card">
          <div className="card-label">Tightness</div>
          <div className="card-value">6.45</div>
        </div>
        <div className="card">
          <div className="card-label">Data Age</div>
          <div className="card-value warning">300s</div>
        </div>
      </div>

      <div className="chart-container">
        <h3>Confidence Decay (vs Baseline)</h3>
        <div style={{ width: '100%', height: 160 }}>
          <ResponsiveContainer>
            <AreaChart data={mockConfidenceData} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="colorHgt" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--accent-primary)" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="var(--accent-primary)" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorCv" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--accent-secondary)" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="var(--accent-secondary)" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ backgroundColor: 'var(--bg-panel)', borderColor: 'var(--border-color)', borderRadius: '8px' }} />
              <Area type="monotone" dataKey="hgt" stroke="var(--accent-primary)" fillOpacity={1} fill="url(#colorHgt)" />
              <Area type="monotone" dataKey="cv_pfa" stroke="var(--accent-secondary)" fillOpacity={1} fill="url(#colorCv)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="chart-container">
        <h3>Quantum-Fuzzy Phase Vector</h3>
        <div style={{ width: '100%', height: 180 }}>
          <ResponsiveContainer>
            <RadarChart cx="50%" cy="50%" outerRadius="80%" data={mockPhaseData}>
              <PolarGrid stroke="var(--border-color)" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} />
              <Radar name="AetherGrid" dataKey="A" stroke="var(--accent-primary)" fill="var(--accent-primary)" fillOpacity={0.3} />
              <Tooltip contentStyle={{ backgroundColor: 'var(--bg-panel)', borderColor: 'var(--border-color)', borderRadius: '8px' }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="export-actions">
        <button className="btn btn-secondary flex-1">
          <FileText size={16} /> JSON
        </button>
        <button className="btn btn-primary flex-2">
          <Download size={16} /> Export Certificate
        </button>
      </div>

      <style jsx>{`
        .safety-dashboard {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .cert-header {
          display: flex;
          align-items: center;
          gap: 1rem;
        }
        
        .cert-header h2 {
          font-size: 1.125rem;
          margin-bottom: 0.125rem;
        }

        .text-muted {
          color: var(--text-muted);
          font-size: 0.75rem;
        }

        .metric-cards {
          display: flex;
          gap: 0.5rem;
        }

        .card {
          flex: 1;
          background: rgba(0,0,0,0.2);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          padding: 0.75rem;
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }

        .card-label {
          font-size: 0.65rem;
          text-transform: uppercase;
          color: var(--text-muted);
          letter-spacing: 0.05em;
        }

        .card-value {
          font-size: 1.125rem;
          font-weight: 600;
          color: var(--text-main);
        }

        .card-value.warning {
          color: var(--warning);
        }

        .chart-container {
          background: rgba(0,0,0,0.1);
          border-radius: 8px;
          padding: 1rem;
          border: 1px solid var(--border-color);
        }

        .chart-container h3 {
          font-size: 0.875rem;
          margin-bottom: 1rem;
          color: var(--text-main);
        }

        .export-actions {
          display: flex;
          gap: 0.5rem;
          margin-top: 0.5rem;
        }

        .flex-1 { flex: 1; }
        .flex-2 { flex: 2; }
      `}</style>
    </div>
  );
}
