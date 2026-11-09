"""Refresh delivery metrics from GitHub on a timer and serve the last result to Prometheus.

GitHub is polled in the background (default every 10 min, ~2-4 requests) rather than on each
scrape, so 30 s scrapes never hit the API's rate limit. Staleness is visible through
delivery_last_refresh_timestamp_seconds and delivery_refresh_success.
"""

import logging
import os
import threading
import time
from datetime import UTC, datetime, timedelta

from prometheus_client import Gauge, start_http_server

from .dora import Report, compute
from .github import GitHub

log = logging.getLogger(__name__)

DEPLOYS = Gauge("delivery_deployments", "Deployments in the window", ["window"])
FREQ = Gauge("delivery_deploys_per_day", "Average deployments per day over the window", ["window"])
LEAD = Gauge("delivery_lead_time_seconds", "Commit-to-deploy lead time", ["window", "quantile"])
CFR = Gauge("delivery_change_failure_ratio", "Share of deployments later reverted", ["window"])
MTTR = Gauge("delivery_time_to_restore_seconds", "Failed deployment to the next good one", ["window", "quantile"])
CI_RUNS = Gauge("delivery_ci_runs", "Main-branch CI runs by conclusion", ["window", "conclusion"])
CI_DUR = Gauge("delivery_ci_duration_seconds", "Main-branch CI run duration", ["window", "quantile"])
OK = Gauge("delivery_refresh_success", "1 if the last GitHub refresh succeeded")
LAST = Gauge("delivery_last_refresh_timestamp_seconds", "Unix time of the last successful refresh")


def _set(g: Gauge, value: float | None, **labels: str) -> None:
    """Set the series, or drop it when there is nothing to report (e.g. no failures yet)."""
    if value is not None:
        g.labels(**labels).set(value)
        return
    try:
        g.remove(*labels.values())
    except KeyError:
        pass


def publish(report: Report, w: str) -> None:
    DEPLOYS.labels(window=w).set(report.deploy_count)
    FREQ.labels(window=w).set(report.deploys_per_day)
    for q in ("0.5", "0.9"):
        _set(LEAD, report.lead_time_quantile(float(q)), window=w, quantile=q)
        _set(CI_DUR, report.ci_duration_quantile(float(q)), window=w, quantile=q)
    _set(MTTR, report.restore_quantile(0.5), window=w, quantile="0.5")
    _set(CFR, report.change_failure_ratio, window=w)
    CI_RUNS.clear()
    for conclusion, n in report.ci_by_conclusion.items():
        CI_RUNS.labels(window=w, conclusion=conclusion).set(n)


def refresh(gh: GitHub, window_days: int) -> None:
    now = datetime.now(UTC)
    window = timedelta(days=window_days)
    # Look back twice the window for source commits and reverts that straddle its start.
    commits = gh.commits(now - 2 * window)
    runs = gh.runs(now - window)
    publish(compute(commits, runs, now, window), f"{window_days}d")


def main() -> None:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
    gh = GitHub(os.environ["GITHUB_REPOSITORY"], token=os.environ.get("GITHUB_TOKEN") or None)
    window_days = int(os.environ.get("WINDOW_DAYS", "30"))
    interval = int(os.environ.get("REFRESH_SECONDS", "600"))
    start_http_server(int(os.environ.get("PORT", "9109")), addr="0.0.0.0")
    stop = threading.Event()
    while not stop.is_set():
        try:
            refresh(gh, window_days)
            OK.set(1)
            LAST.set(time.time())
            log.info("refreshed delivery metrics")
        except Exception:
            OK.set(0)
            log.exception("refresh failed")
        stop.wait(interval)


if __name__ == "__main__":
    main()
