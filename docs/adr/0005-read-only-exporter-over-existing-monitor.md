# 5. The exporter reads the existing monitor API; it does not touch the recorder or its database

Date: 2026-11-09 · Status: accepted

## Context
The recorder is the system of record for live data and must not be restarted or reconfigured to
add observability. It already ships a monitor service with a JSON `/api/status` (per-stream age,
rows per minute, state, recorder container state).

## Decision
A separate exporter polls that endpoint on each Prometheus scrape and translates it to metrics.
No database credentials, no changes to the recorder, no writes anywhere. Fetching on scrape
(rather than on a timer) means the metric is exactly as old as the scrape, and a failed read shows
up as `well_up 0` on that same scrape.

## Consequences
- The platform can be built, broken and rebuilt without any risk to data collection.
- We inherit the monitor's own cache (exported as `well_monitor_cache_age_seconds`).
- If the monitor's JSON shape changes, the exporter degrades to missing series, not a crash; the
  `FreshnessExporterAbsent` and SLO alerts cover the gap.
