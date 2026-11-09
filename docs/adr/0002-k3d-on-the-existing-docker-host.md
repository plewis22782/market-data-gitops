# 2. Run k3s inside Docker (k3d) on the existing compute host

Date: 2026-11-09 · Status: accepted

## Context
The cluster runs on a host ("Redfish": 72 threads, ~250 GB RAM) that already runs production
Docker workloads: a backtest optimizer, a local LLM stack, and a Cloudflare tunnel. Installing k3s
natively means root, a systemd service, a CNI that rewrites iptables, and coexistence questions
with the host's Docker and ufw rules. A mistake there takes down workloads that have nothing to
do with this project.

## Decision
Run k3s in Docker with k3d: one server and two agents, NodePorts published on the host for
ArgoCD, Grafana and Prometheus, Traefik disabled (no ingress needed on a LAN). Tools install
into `~/.local/bin` with sha256 verification; no sudo.

## Consequences
- Zero host-level changes. `cluster/teardown.sh` returns the host to exactly where it was.
- The whole cluster is disposable, which makes the disaster-recovery drill (rebuild from git)
  cheap to run for real.
- Not a production topology: node failure means the host failed. Acceptable for a single-host
  lab; a multi-node move would supersede this ADR with native k3s or a managed cluster.
- The cluster reaches the recorder monitor over the LAN; no inbound ports from the internet.
