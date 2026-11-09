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

## Drill 2 — 2026-11-09 18:54Z (during RTH, after ADR 0006)

| Phase | Time |
|---|---|
| Teardown | 8 s |
| Bootstrap (cluster + ArgoCD) | 121 s |
| ArgoCD sync, 5 Applications Healthy (sync waves now enforced) | 170 s |
| First SLO evaluation | 121 s more |
| **Total (RTO)** | **420 s, objective met** |

**RPO: met.** The oldest Prometheus sample was 18:43:47Z before teardown and still 18:43:47Z after;
SLO samples in the last hour went 21 → 22 instead of to zero.

Observed cost: the platform is blind while it's down (~7 min here). Those evaluations are absent,
not counted as good or bad, and `FreshnessExporterAbsent` covers a longer outage.

Getting here needed three fixes, all found by rebuilding rather than by reading:
1. The Prometheus operator rejects a `storageClassName` without a StorageClass object, even for a
   pre-bound PV → `gitops/platform/storageclass.yaml`.
2. The kubelet creates `subPath` directories as root on hostPath, and Prometheus runs as uid 1000
   → `disableMountSubPath: true`.
3. Sync waves between child Applications only work when ArgoCD has a health check for
   `Application` resources → `cluster/argocd-values.yaml`.
