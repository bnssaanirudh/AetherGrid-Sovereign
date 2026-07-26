# Artifact Security Policy

## Supply-Chain Security
AetherGrid Sovereign uses automated CycloneDX SBOM generation across all build pipelines. SBOMs are archived in the `artifacts/sboms/` directory and must be reviewed prior to major releases for vulnerable transitive dependencies.

## Model Checksum Verification
To prevent arbitrary code execution during `torch.load()` or `pickle` deserialization, the AetherGrid backend employs strict checksum validation.

**Workflow:**
1. A trained model is hashed (SHA-256) by the CI pipeline.
2. The hash is committed to `artifacts/registry/manifest.json`.
3. In production, `ModelRegistry` compares the physical file's checksum against the manifest.
4. If there is a mismatch, a `SecurityError` is raised and the server aborts, preventing potential Remote Code Execution (RCE).

## Dependency Update Policy
- Dependabot is configured for automated PRs on all `packages/` and `frontend/` dependencies.
- Production deployments prohibit `latest` tags; all base images must use SHA256 pinned digests.
- Secrets must never be committed; `detect-secrets` or GitHub Secret Scanning runs on all PRs.
