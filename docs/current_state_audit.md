# Forensic Audit of AetherGrid-Sovereign

This document outlines the state of every major module in the repository before migrating to the production-ready monorepo layout.

## Major Module Audits

### `core/graph_constructor.py`
- **Current Behavior**: Generates synthetic `HeteroData` graphs for road, power, hospital, and citizen node types with random features and edge links.
- **Proposal Requirement**: Support versioned domain schemas (`NodeRecord`, `EdgeRecord`, etc.) representing road segments, power nodes, weather station cells, POI/social nodes, and control nodes. Keep hospital/citizen as migration aliases. Support spatial coordinates and CRS metadata.
- **Correctness Risk**: High risk of importing raw dict/tensors without valid structural validation. Ambiguous node types.
- **Migration Decision**: Move to `packages/graph_builder`, implement strict Pydantic parsing, and add CRS metadata fields.
- **Owner Prompt**: Refactor imports to `packages/graph_builder`.

### `core/fuzzy_attention.py` and `quantum_fuzzy_fusion.py`
- **Current Behavior**: Implements Intuitionistic Fuzzy Set (IFS) attention on PyG graphs. Contains placeholders for quantum phase shift decays.
- **Proposal Requirement**: Support both IFS and Pythagorean Fuzzy Set (PFS) semantics with fuzzy-family constraint validation. Provide clean complex tensor and phase-generator interfaces.
- **Correctness Risk**: The current implementation has unvalidated fuzzy boundaries and assumes IFS without a fallback or comparative validation.
- **Migration Decision**: Move to `packages/models` and establish strict fuzzy constraint validation (sum of membership + non-membership <= 1 for IFS, squared sum <= 1 for PFS).
- **Owner Prompt**: Update fuzzy logic checks and add PFS validation.

### `optimization/` (Chaotic maps, Q-AVOA NAS, nas_search)
- **Current Behavior**: Runs Q-AVOA and Chaotic NAS optimization to search HGT hyperparameters.
- **Proposal Requirement**: Archive Q-AVOA and Chaotic NAS into a legacy/experimental namespace (`packages/aethergrid_legacy/optimization/`). HGT should run behind a legacy command but not be part of the primary architecture. The primary quantum focus is VQC phase generator, not quantum-inspired optimization.
- **Correctness Risk**: The NAS controller evaluates models with random masks, which suffers from severe temporal data leakage and runs slow proxy epochs.
- **Migration Decision**: Move to `packages/aethergrid_legacy` and keep runnable only behind legacy flags.
- **Owner Prompt**: Isolate optimization modules.

### `watchdog/sovereign_watchdog.py`
- **Current Behavior**: Performs basic type, shape, and NaN checks on incoming graphs.
- **Proposal Requirement**: Production watchdog needs versioned schema validation, quarantine reporting, and silent synthetic fallback prevention.
- **Correctness Risk**: Falls back silently on synthetic data when external data adapters fail, hiding production failures.
- **Migration Decision**: Move to `packages/watchdog` and raise errors on adapter failure when the production profile is active.
- **Owner Prompt**: Restructure watchdog and add profile guards.

### `experiments/train.py`
- **Current Behavior**: Trains HGT using continuous labels coerced into F1 metrics. Random node split mask as splits.
- **Proposal Requirement**: Reject invalid label/metric combinations. Split data using leakage-safe event/snapshot splits. Safe, versioned checkpointing.
- **Correctness Risk**: Continuous-to-F1 label coercion renders evaluation metrics meaningless. Random masks cause future leakage in temporal series.
- **Migration Decision**: Split into `packages/training` and `packages/evaluation`. Explicit task schema validation.
- **Owner Prompt**: Redesign dataset splits and model validation loop.
