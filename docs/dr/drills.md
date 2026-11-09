# Disaster-recovery drills

**Objectives:** RTO 15 minutes (platform back and the SLO evaluating again after total cluster
loss). RPO for metrics: no more than the scrape interval (30 s) of history lost.

**Procedure:** `cluster/teardown.sh` followed by `cluster/bootstrap.sh`, timed from teardown until
all ArgoCD Applications are Synced/Healthy and `well:slo_spx_fresh:total` returns a sample.
Run on a live trading day; the recorder being watched is never touched.

## Drill 1 — 2026-11-09 18:14Z (during RTH)

| Phase | Time |
|---|---|
| Teardown | 8 s |
| Bootstrap (cluster + ArgoCD) | 138 s |
| ArgoCD sync to all Healthy | 154 s |
| First SLO evaluation | immediate |
| **Total (RTO)** | **300 s, objective met** |

**RPO: failed.** Every Prometheus sample was lost (oldest sample after rebuild: 18:18:11Z). The
30-day SLO window restarted. Finding → ADR 0006 (host-backed PV).

Also noted: ArgoCD and Grafana admin passwords are regenerated on rebuild (by design; they're
never in git).
