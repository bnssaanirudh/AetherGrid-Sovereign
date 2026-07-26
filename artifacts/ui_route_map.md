# AetherGrid Sovereign - UI Route Map

The Digital Twin Next.js Application follows a flat, component-driven route architecture to maintain optimal performance for geospatial rendering.

## 1. Live Twin Dashboard
- **Route**: `/` (Root)
- **Primary Component**: `page.tsx`
- **Sub-components**: 
  - `DigitalTwinMap.tsx`: Core MapLibre/Deck.gl WebGL rendering surface.
  - `ScenarioBuilder.tsx`: Left-panel configuration form for Trigger IDs, Weather snapshots, and hesitation margins.
  - `SafetyDashboard.tsx`: Conditional left-panel display showing prediction certificates (e.g. `cert_success_01`, trace: `trace_01`).
- **Data Flow**: Submits parameters to backend `/scenarios/async`, polls Job ID, and retrieves Quantum-Fuzzy bounds.

## 2. Data Quality & Ingestion
- **Route**: `/data`
- **Primary Component**: `data/page.tsx`
- **Purpose**: Displays health metrics of raw data ingestion before graph construction.
- **Key Metrics**: 
  - Live Sensors (Online %)
  - Quarantined Records
  - Real-time ingestion logs from OpenStreetMap and WeatherBench.

## 3. Research Lab & Model Comparison
- **Route**: `/research`
- **Primary Component**: `research/page.tsx`
- **Purpose**: Offline benchmark evaluation interface.
- **Key Features**: 
  - Side-by-side table comparing `AetherGrid-Q-HGT` vs `CV-PFA MLP` and `GCN-Baseline`.
  - Metrics displayed: Calibration ECE, Bound Coverage %, Inference Latency.

## 4. Shared Layouts
- **Component**: `layout.tsx` & `Sidebar.tsx`
- **Function**: Provides the global `Sidebar` navigation, persistent across all routes to prevent full-page reloads and preserve MapGL state where possible. Includes Content-Security-Policy definitions.
