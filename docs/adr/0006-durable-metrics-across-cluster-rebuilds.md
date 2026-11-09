# 6. Keep Prometheus data on the host so a cluster rebuild doesn't reset the SLO

Date: 2026-11-09 · Status: accepted

## Context
DR drill 1 (docs/dr/drills.md) rebuilt the cluster from git in 5 minutes, but Prometheus lived on
k3s's local-path volume inside the node containers, so the teardown deleted every sample. The
30-day SLO window and its error budget restarted from zero. An SLO that resets whenever the
platform is rebuilt doesn't hold anyone to anything.

## Decision
- Every k3d node mounts a host directory (`$RACK_DATA_DIR`, default `~/k3d-rack-data`) at `/data`.
- A static PersistentVolume (`gitops/platform/prometheus-pv.yaml`, `Retain`, class `rack-retained`)
  points at `/data/prometheus` and is pre-bound by `claimRef` to the operator's PVC name.
- The `platform` Application syncs first (wave -1) and never prunes, so the PV can't be deleted by a sync.
- `cluster/teardown.sh` deletes the cluster and keeps `$RACK_DATA_DIR`.

## Consequences
- The RPO for metrics becomes "since the last scrape before teardown" instead of "everything".
- The data is still on one host's disk: losing Redfish loses it. Off-host copies (remote write or
  snapshots to the other server) are the next step if that RPO matters.
- `hostPath` ties the workload to this single-host topology, which ADR 0002 already accepts.
