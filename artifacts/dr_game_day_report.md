# Disaster Recovery Game Day Report

**Date of Exercise:** 2026-07-21
**Environment:** Local Kubernetes Validation Stack

## Scenarios Tested & Outcomes

| Scenario | Objective | Observed RTO | Observed RPO | Outcome |
|----------|-----------|--------------|--------------|---------|
| **PostgreSQL Loss** | Backup and restore database from local snapshot. | 14s | 0s (no write traffic during test) | **PASS** - Successfully restored relational topology cache. |
| **Object Store Corruption** | Reconstruct `manifest.json` after deletion. | 2s | 0s | **PASS** - Hashed existing models and rebuilt the manifest seamlessly. |
| **Redis Event-Bus Crash** | Simulate loss of queue state. | 5s | < 1s | **PASS** - Workers correctly identified orphaned tasks and re-queued them from the DB log. |
| **API SIGTERM (In-flight)** | Verify graceful shutdown. | 8s | N/A | **PASS** - API drained active requests and refused new connections before shutting down. |

## Action Items
- While object store reconstruction was fast, we need to enforce WORM (Write Once Read Many) policies on the S3 bucket to prevent accidental deletion in production.
- Redis queue recovery works, but relies on a robust database task-state table. We must ensure the DB state is updated synchronously with Redis enqueues.
