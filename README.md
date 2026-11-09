# market-data-gitops

GitOps platform for observing a live market-data recorder: a Kubernetes cluster, a Python
exporter, a Helm chart, ArgoCD, GitHub Actions CI, and a tested SLO with an error budget.

The recorder it watches is a production system I run on my own rack: it streams live index,
futures and options quotes over WebSocket into PostgreSQL/TimescaleDB around the clock. That
system lives in its own (private) repositories. This repo is the platform layer around it, built
in the open.

## What's here

```mermaid
flowchart LR
  dev[PR / push to main] --> ci[GitHub Actions<br/>ruff · pytest · promtool · helm lint · kubeconform · shellcheck]
  ci --> img[ghcr.io image<br/>sha-tagged]
  ci -- commits new tag --> repo[(gitops/values)]
  repo --> argo[ArgoCD<br/>app of apps]
  argo --> fe[freshness-exporter]
  argo --> kps[kube-prometheus-stack<br/>Prometheus · Alertmanager · Grafana]
  fe -- reads /api/status --> mon[recorder monitor<br/>existing, read-only]
  kps -- scrapes --> fe
```

| Path | What it is |
|---|---|
| `apps/freshness-exporter/` | Python Prometheus exporter. Reads the recorder monitor's `/api/status` on each scrape and exports per-stream age, rows/min and state, recorder up/restarts, and an RTH flag. 12 unit tests. |
| `charts/freshness-exporter/` | Helm chart: Deployment (non-root, read-only root FS), Service, ServiceMonitor, PrometheusRule, Grafana dashboard. |
| `charts/freshness-exporter/rules/` | SLO recording rules and multiwindow burn-rate alerts, unit-tested with `promtool test rules`. |
| `gitops/` | ArgoCD app of apps, the Applications, and per-environment values. CI writes the image tag here; ArgoCD does the deploy. |
| `cluster/` | k3d cluster config, pinned tool versions, checksum-verified tool install, bootstrap and teardown. |
| `docs/adr/` | Architecture decision records. Start with [0001](docs/adr/0001-record-architecture-decisions.md). |
| `docs/runbooks/` | What to do when an alert fires. |

## The SLO

> During US regular trading hours, the SPX stream's last event is under 60 seconds old for
> **99.5%** of 30-second evaluations over a rolling 30 days.

That is about 41 minutes of budget per 30 days (~21 sessions × 390 RTH minutes × 0.5%). An unreachable monitor
counts as bad, and time outside RTH (the weekend stop, the daily CME halt) is excluded. Alerts are
multiwindow burn rates (14.4x over 1 h + 5 m pages, 6x over 6 h + 30 m opens a ticket), so they
fire on user impact, not on a single slow scrape. Reasoning in
[ADR 0004](docs/adr/0004-recorder-freshness-slo.md).

## Path to production

1. Open a PR. CI runs lint, unit tests, rule tests, chart lint and render, schema validation, and shellcheck.
2. Merge to `main`. CI builds the image, pushes `ghcr.io/plewis22782/freshness-exporter:sha-<commit>`,
   and commits that tag to `gitops/values/freshness-exporter.yaml`.
3. ArgoCD sees the commit and syncs. CI never holds cluster credentials.
4. Rollback is `git revert` of the tag commit. ArgoCD syncs the previous image.

## Run it

```bash
cluster/install-tools.sh     # k3d, kubectl, helm into ~/.local/bin, sha256-verified
cluster/bootstrap.sh         # cluster + ArgoCD; everything else comes from git
```

ArgoCD on `:8441`, Grafana on `:8442`, Prometheus on `:8443` of the host. `cluster/teardown.sh`
removes everything. Nothing outside the cluster is touched ([ADR 0002](docs/adr/0002-k3d-on-the-existing-docker-host.md)).

## Roadmap

- [ ] Disaster-recovery drill: delete the cluster, rebuild from git, and record time to restore against a stated RTO.
- [ ] Delivery metrics from GitHub Actions: lead time, deploy frequency, change failure rate, time to restore.
- [ ] Terraform for the GitHub side: branch protection, required checks, environments.
- [ ] Alertmanager routing to a real receiver.
- [ ] Exchange holiday calendar for the RTH flag (today a holiday counts as RTH; see ADR 0004).
- [ ] Second SLO for option-contract coverage, not just the index stream.
