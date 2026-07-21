"use client";

import React, { useState } from 'react';
import { Play, Settings2, ShieldAlert } from 'lucide-react';
import apiClient from '@/lib/api/client';

export default function ScenarioBuilder() {
  const [city, setCity] = useState("chicago");
  const [hazard, setHazard] = useState("extreme_heat");
  const [loading, setLoading] = useState(false);

  const runScenario = async () => {
    setLoading(true);
    try {
      // Example of using the generated OpenAPI client
      // We are just calling a generic endpoint to show integration
      const { data, error } = await apiClient.GET("/api/v1/health");
      
      // Simulate heavy compute
      await new Promise(r => setTimeout(r, 2000));
      
      if (error) {
        console.error("API Error:", error);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="scenario-builder">
      <h2>Configure Scenario</h2>
      <p className="text-muted">Set boundary conditions for the Quantum-Fuzzy HGT model.</p>
      
      <div className="form-group">
        <label>City Digital Twin Snapshot</label>
        <select value={city} onChange={(e) => setCity(e.target.value)}>
          <option value="chicago">Chicago (Urban-KG)</option>
          <option value="toy">Toy Grid Network</option>
          <option value="new_york">New York City</option>
        </select>
      </div>

      <div className="form-group">
        <label>Atmospheric Hazard</label>
        <select value={hazard} onChange={(e) => setHazard(e.target.value)}>
          <option value="extreme_heat">Extreme Heat Wave</option>
          <option value="hurricane">Hurricane / Flooding</option>
          <option value="grid_attack">Cyber-Physical Attack</option>
        </select>
      </div>
      
      <div className="form-group">
        <label>Sensor Dropout Rate (Hesitation Margin)</label>
        <input type="range" min="0" max="100" defaultValue="15" className="slider" />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginTop: '0.5rem', color: 'var(--text-muted)' }}>
          <span>0%</span>
          <span>15%</span>
          <span>100%</span>
        </div>
      </div>

      <div className="actions">
        <button className="btn btn-primary w-full" onClick={runScenario} disabled={loading}>
          {loading ? (
            <span className="glow-effect">Running Simulation...</span>
          ) : (
            <>
              <Play size={16} /> Run Q-AVOA Simulation
            </>
          )}
        </button>
        <button className="btn btn-secondary w-full">
          <Settings2 size={16} /> Advanced Parameters
        </button>
      </div>

      <style jsx>{`
        .scenario-builder {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        h2 {
          font-size: 1.25rem;
          margin-bottom: 0.25rem;
        }

        .text-muted {
          color: var(--text-muted);
          font-size: 0.875rem;
          margin-bottom: 1rem;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        label {
          font-size: 0.875rem;
          font-weight: 500;
          color: var(--text-main);
        }

        select {
          background: rgba(0, 0, 0, 0.3);
          border: 1px solid var(--border-color);
          color: var(--text-main);
          padding: 0.75rem;
          border-radius: 6px;
          font-family: inherit;
          font-size: 0.875rem;
          outline: none;
          transition: border-color 0.2s;
        }

        select:focus {
          border-color: var(--accent-primary);
        }

        .slider {
          -webkit-appearance: none;
          width: 100%;
          height: 4px;
          border-radius: 2px;
          background: var(--border-color);
          outline: none;
        }

        .slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: var(--accent-primary);
          cursor: pointer;
          box-shadow: 0 0 10px var(--accent-primary-dim);
        }

        .actions {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          margin-top: 1rem;
        }

        .w-full {
          width: 100%;
          padding: 0.75rem;
        }
      `}</style>
    </div>
  );
}
