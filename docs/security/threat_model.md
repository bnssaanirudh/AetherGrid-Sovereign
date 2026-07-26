# AetherGrid Sovereign: Threat Model (STRIDE)

## 1. Spoofing
- **Threat**: Falsified sensor data ingested from compromised IoT grids.
- **Mitigation**: Watchdog node quarantine limits the influence of drifting inputs. Cryptographic signatures required on sensor payloads (future roadmap). API requires JWT authentication.

## 2. Tampering
- **Threat**: Model artifact substitution (e.g. poisoning weights).
- **Mitigation**: `ModelRegistry` enforces SHA-256 checksums matching the CI/CD-generated manifest. S3 buckets enforcing WORM policies.

## 3. Repudiation
- **Threat**: Operator denies initiating a cascade intervention.
- **Mitigation**: All scenario jobs and bound predictions are logged with `job_id`, timestamp, and the requester's JWT subject claim in PostgreSQL.

## 4. Information Disclosure
- **Threat**: Data exfiltration of sensitive urban topology or sensor data.
- **Mitigation**: The API enforces RBAC. Unauthenticated access is blocked. Front-end uses strict Content-Security-Policy (CSP). TLS 1.3 mandated for all transit.

## 5. Denial of Service
- **Threat**: Malicious scenario requests (e.g., massive ego graph queries) exhausting GPU resources.
- **Mitigation**: Rate limiting implemented on the API. Payload limits restricted to `< 5000` nodes per scenario request. Async queueing isolates the web layer from the inference workers.

## 6. Elevation of Privilege
- **Threat**: Safety certificate tampering or unauthorized role escalation.
- **Mitigation**: Certificates are cryptographically signed by the backend and verified on the client. RBAC enforces `viewer` vs `operator` roles.

## Accepted Risks
- **Supply-Chain Zero-Days**: While SBOMs are generated, 0-day exploits in PyTorch/FastAPI remain a risk. Addressed via regular container scanning and prompt patching.
