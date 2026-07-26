# AetherGrid Sovereign: Claim-Evidence Matrix

This matrix maps every core proposal deliverable to its concrete evidence (code, tests, and artifacts). Any marketing claim lacking evidence has been removed.

| Deliverable | Code Implementation | Tests & Validation | Trace/Run ID | Known Limitations |
|-------------|---------------------|--------------------|--------------|-------------------|
| **Graph Construction** | `packages/aethergrid_core/src/aethergrid_core/data/event_dataset.py` | `tests/core/test_dataset.py` | `snapshot_graph_01` | Raw topologies are static for offline runs; streaming graph mutations not fully implemented. |
| **Fuzzy State & CV-PFA** | `packages/models/src/models/hetero_transformer.py` | `run_prompt5_smoke.py` | `trace_cvpfa_02` | CV-PFA assumes independent hazard priors which may slightly underestimate correlated cascading risks. |
| **VQC Phase Generator** | `packages/models/src/models/vqc_generator.py` | `run_prompt6_smoke.py` | `trace_vqc_01` | Pennylane simulator only. Real quantum hardware execution not integrated. |
| **Ego Sampler** | `packages/aethergrid_core/src/aethergrid_core/data/ego_sampler.py` | `tests/core/test_sampler.py` | `trace_ego_01` | Deep cascades (depth > 5) cause latency spikes during real-time inference. |
| **Cascade Tasks** | `packages/models/src/models/multi_task_heads.py` | `run_prompt6_smoke.py` | `trace_cascade_01` | Intervention ranking uses naive greedy selection rather than a true constraint solver. |
| **Theorem & Bound** | `packages/theory/src/theory/bounds.py`, `phase_theorem.py` | `tests/theory/test_bounds.py` | `trace_theorem_01` | Bounds are provably tight only in tree-like substructures, loose in highly clustered graph topologies. |
| **Calibration & Uncertainty** | `packages/evaluation/src/evaluation/bound_validation.py` | `run_prompt6_smoke.py` | `trace_calib_01` | Abstention threshold is static; dynamic thresholding based on operator workload is missing. |
| **Baselines & Ablations** | `run_prompt6_smoke.py` | Benchmark suites (GCN vs MLP vs Q-HGT) | `trace_baseline_01` | Baselines lack sophisticated hyperparameter tuning, potentially favoring the proposed Q-HGT slightly. |
| **API & Data Platform** | `backend/app/main.py`, `backend/app/api/` | `tests/backend/test_api.py` | `trace_api_01` | RBAC is implemented via mock tokens; no external OIDC provider configured. |
| **Dashboard** | `frontend/src/app/`, `frontend/src/components/` | Puppeteer Accessibility Scans | `trace_ui_01` | Map layers use static mock data until full WebSocket streaming is merged to production. |
| **Reproducibility Package**| `artifacts/research_package/`, `docs/manuscript_asc.md` | Final Release Handoff Checks | `trace_repro_01` | Relies on local Python environment determinism (requires exact python version matching). |

## Audited Removed Claims
- Removed claims of "millisecond real-time quantum supremacy" as VQC is purely simulated.
- Removed claims of "infinite scale graph ingestion" as the Ego Sampler is bounded by memory constraints.
- Removed claims of "certified military-grade encryption" from API docs, replaced with "TLS 1.3 standard transit encryption".
