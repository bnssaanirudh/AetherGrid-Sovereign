# AetherGrid Operations Runbook

## 1. Deploy / Upgrade / Rollback
- **Deploy**: Merges to `main` auto-deploy to staging. To deploy to production, tag the release `vX.Y.Z`. CI/CD builds signed containers. Apply via `kubectl apply -k deploy/kubernetes/base`.
- **Upgrade**: Ensure Postgres schema migrations (`alembic upgrade head`) are run before rotating backend pods.
- **Rollback**: Identify the previous healthy tag. Run `kubectl set image deployment/aethergrid-backend backend=aethergrid-backend:<old-tag>`. Downgrade DB if necessary.

## 2. Data Source Failure & Quarantine Spike
- **Symptom**: Data Quality dashboard shows > 5% sensors offline or high quarantined records.
- **Action**: Check `sovereign_watchdog` logs for parsing errors. If external APIs (e.g. WeatherBench) changed schema, disable the adapter temporarily and rely on the last known good snapshot (stale-sensor mode).

## 3. Model Latency Regression
- **Symptom**: Inference takes > 500ms for medium ego graphs.
- **Action**: Ensure VQC cache is hitting in Redis. If the Quantum simulator is overloaded, scale the backend deployment horizontally.

## 4. Calibration Drift & Bound-Coverage Regression
- **Symptom**: Bound coverage drops below 95% on the Research Lab page.
- **Action**: The CV-PFA module's temperature scaling parameters are stale. Trigger the offline retraining DAG via `run_offline_build.sh` and deploy a new model artifact.
