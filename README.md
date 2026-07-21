# AetherGrid Sovereign

![AetherGrid Release](https://img.shields.io/badge/Release-1.0.0--rc1-blue.svg)
![Coverage](https://img.shields.io/badge/Coverage-99.0%25-green.svg)

**AetherGrid Sovereign** is an enterprise-grade digital twin platform designed for predictive infrastructure management and autonomous grid operation. Leveraging Conformal-Venn Prediction and Q-HGT, it provides mathematically guaranteed safety bounds for cascading infrastructure failures.

## Core Architecture

### 1. Sovereign Watchdog
An automated safety policy enforcement layer ensuring all grid operations stay strictly within predefined operational phase bounds and safety thresholds. It acts as the final gatekeeper against cascading failures.

### 2. Conformal Prediction Engine
A statistical bounds computation engine that provides mathematically guaranteed confidence intervals for dynamic urban infrastructure loads, rejecting unsafe automated interventions when bounds are loose.

### 3. Live Grid Ingestion
Real-time streaming infrastructure providing massive-scale ingestion of urban telemetry data, IoT sensors, and latency-sensitive state changes.

### 4. Digital Twin & Scenario Lab
High-performance geospatial mapping layer utilizing WebGL to visualize millions of nodes, power flows, and infrastructure health in real-time. The Scenario Lab allows operators to run what-if simulations against live data without affecting the physical grid.

## Quickstart

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+

### Running the Enterprise Platform
1. **Start the Core Engine & API**
   ```bash
   docker-compose up --build -d
   ```

2. **Start the Frontend Application**
   ```bash
   cd website
   npm install
   npm run dev
   ```
   Access the Operator Dashboard at `http://localhost:3000/dashboard`.
   View the Public Landing Page at `http://localhost:3000`.

### Running the Deterministic Demonstration
To run a standalone offline demonstration of the Q-HGT versus baseline models:
```bash
bash run_final_demo.sh
```

## Documentation
- [Architecture C4 Models](docs/architecture/system_c4.md)
- [Operations Runbooks](docs/runbooks/operations.md)
- [Threat Model](docs/security/threat_model.md)
- [Claim Evidence Matrix](artifacts/claim_evidence_matrix.md)

## License
MIT License. See `LICENSE` for details.
