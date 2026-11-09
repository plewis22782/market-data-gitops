# 4. Recorder freshness SLO: 99.5% over 30 days, RTH only, burn-rate alerting

Date: 2026-11-09 · Status: accepted

## Context
The recorder's users are strategies and dashboards that need current prices during the trading
session. The failures that actually hurt were all "data stopped arriving and nothing said so":
a stream silently dark for 2.5 days, a reconnect loop that tripped the vendor's session cap, a
futures feed dark after the daily halt. A CPU or container-up alert would have caught none of them.

## Decision
- **SLI:** the share of 30-second evaluations during US RTH (09:30–16:00 ET, Mon–Fri) in which the
  SPX stream's last event is under 60 s old. SPX is the stream every downstream consumer needs.
- **Monitor unreachable counts as bad.** If we can't see it, we can't claim it was fresh.
- **Outside RTH is excluded.** The recorder is stopped on weekends on purpose and the CME halts daily.
- **Objective:** 99.5% over a rolling 30 days, about 41 minutes of budget per 30 days (~21 sessions × 390 RTH minutes).
- **Alerts:** multiwindow burn rates per the Google SRE workbook: page at 14.4x (1 h and 5 m),
  ticket at 6x (6 h and 30 m). Plus an alert when the exporter itself disappears.
- Rules are unit-tested with `promtool test rules` in CI, including the excluded and unreachable cases.

## Consequences
- Exchange holidays aren't modeled yet, so a holiday burns budget. Fix: a holiday calendar.
  Don't loosen the objective to hide it.
- The SLI is per-evaluation, not per-request: Prometheus needs at least 30 days of retention (set to 45 d).
- 60 s is deliberately loose. Normal age is under 10 s, so the threshold catches outages, not jitter.
