export const siteConfig = {
  name: "AetherGrid Sovereign",
  description: "The Sovereign Cryptographic Mesh for Decentralized Coordination.",
  url: "https://aethergrid.ai",
  links: {
    github: "https://github.com/aethergrid/sovereign",
    docs: "/docs",
    dashboard: "/dashboard",
  },
};

export const dependencies = [
  { name: "PyTorch Geometric" },
  { name: "PennyLane" },
  { name: "FastAPI" },
  { name: "PostgreSQL" },
  { name: "PostGIS" },
  { name: "MapLibre" },
  { name: "Docker" },
];

export const capabilities = [
  {
    id: "routing",
    title: "Sovereign Peer-to-Peer Routing",
    description: "Real-time mesh networking powered by localized node discovery. Nodes dynamically route cryptographic claims across peer networks, avoiding single-point bottlenecks and guaranteeing route resilience under severe network partitions. Every hop is mathematically verified for integrity before propagation.",
    icon: "Network",
    research: false,
  },
  {
    id: "claims",
    title: "Cryptographic Claim Discipline",
    description: "The entire security layer is governed by a strict claim validation mechanism. Proofs are structured as immutable, signed assertions that can be audited instantly without exposing user credentials or private payloads. This zero-trust architecture ensures data provenance at the edge.",
    icon: "ShieldCheck",
    research: false,
  },
  {
    id: "threat",
    title: "Modular Threat Modeling",
    description: "Integrates direct references to repository artifacts, actively defending against denial of service, network hijacking, and partition exploits. The Sovereign Watchdog continuously evaluates node behavior against predefined STRIDE heuristics.",
    icon: "Activity",
    research: false,
  },
  {
    id: "fuzzy",
    title: "Fuzzy-Uncertainty-Aware Attention",
    description: "CV-PFA mechanisms inherently encode sensor noise and stale telemetry into the attention weights. Instead of discarding noisy data, the transformer dampens its influence dynamically based on conformal confidence intervals.",
    icon: "BrainCircuit",
    research: false,
  },
  {
    id: "vqc",
    title: "VQC Phase Generator",
    description: "Simulates variational quantum circuits to embed high-dimensional node features into complex Hilbert space. By projecting urban grid states into quantum amplitudes, we capture non-linear topological dependencies unattainable by classical ML.",
    icon: "Atom",
    research: true,
  },
  {
    id: "intervention",
    title: "Intervention Ranking",
    description: "Evaluates the optimal topological modifications to maximize grid resilience. Running counterfactual simulations across millions of edges, the engine ranks physical interventions based on ROI and cascading prevention probability.",
    icon: "ListOrdered",
    research: false,
  }
];

export const useCases = [
  {
    id: "power-grid",
    label: "Power Grid Resilience",
    title: "Preventing wide-area blackouts via microgrid islanding",
    description: "AetherGrid simulates load-shedding and cascading failures when key substations trip. By fusing real-time telemetry from SCADA systems with our graph transformers, the network autonomously identifies which switches to open, preemptively islanding critical microgrids before the cascade propagates.",
  },
  {
    id: "storm-response",
    label: "Storm & Hazard Response",
    title: "Dynamic threat modeling during extreme weather",
    description: "During hurricanes or extreme flooding, static GIS systems fail to capture cascading dependencies (e.g., a flooded road prevents fuel delivery to a backup generator). By fusing live atmospheric hazards with physical infrastructure graphs, the system flags vulnerable assets hours before physical impact.",
  },
  {
    id: "investment",
    label: "Infrastructure Investment",
    title: "Data-driven capital allocation for resilience",
    description: "Rank structural interventions—such as burying specific transmission lines, upgrading critical transformers, or building redundant fiber routes—based on their simulated Return on Investment (ROI) for overall network robustness across thousands of Monte Carlo scenarios.",
  }
];

export const evidenceFeed = [
  {
    date: "July 2026",
    title: "STRIDE Threat Model & Security Audit",
    type: "Security Report",
    link: "docs/security/threat_model.md",
  },
  {
    date: "July 2026",
    title: "PennyLane Q-HGT Load Profile",
    type: "Benchmark",
    link: "artifacts/performance_report.md",
  },
  {
    date: "July 2026",
    title: "Digital Twin Architecture (C4)",
    type: "Architecture",
    link: "docs/architecture/system_c4.md",
  }
];
