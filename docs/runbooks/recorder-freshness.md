# Runbook: recorder freshness alerts

## RecorderFreshnessBudgetFastBurn (page) / SlowBurn (ticket)
SPX data has been stale (≥ 60 s) for an unsustainable share of RTH.

1. Grafana → *Recorder freshness SLO*. Is it one stream or all of them? Is `well_up` 0?
2. `well_up` 0: the monitor is unreachable. Check the monitor container and the network path
   before assuming the recorder is down.
3. One stream dark, others fresh: a partial subscription loss. Compare with the option-contracts
   row rate. If options still flow but the index is dark, that is the partial-staleness pattern.
4. Everything dark: check the recorder container and its log for reconnect loops or
   session-limit errors. **Don't restart repeatedly.** Back-to-back reconnects are what trip the
   vendor's session cap. One clean restart, then wait.
5. Afterwards: write the postmortem and add a guard or a test so the same failure can't recur silently.

## FreshnessExporterAbsent (ticket)
Prometheus has no samples from the exporter, so the SLO is blind (no budget is burned while
absent). Check the `freshness-exporter` pod in namespace `well`, its ServiceMonitor, and the
Prometheus targets page.
