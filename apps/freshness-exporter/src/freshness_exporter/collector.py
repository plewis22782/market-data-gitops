"""Scrape-time collector: each Prometheus scrape triggers one read of the monitor's /api/status.

Fetching on scrape (not on a background timer) keeps the exported numbers exactly as old
as the scrape says they are, and means an unreachable monitor shows up as well_up 0 on
the very scrape that failed.
"""

import logging
import time
from collections.abc import Callable, Iterator
from datetime import UTC, datetime

import httpx
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.registry import Collector

from .rth import in_rth

log = logging.getLogger(__name__)

STATES = ("fresh", "stale", "dark", "unknown")


class StatusCollector(Collector):
    def __init__(
        self,
        monitor_url: str,
        timeout_s: float = 5.0,
        client: httpx.Client | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.url = monitor_url.rstrip("/") + "/api/status"
        self.client = client or httpx.Client(timeout=timeout_s)
        self.clock = clock

    def fetch(self) -> dict:
        r = self.client.get(self.url)
        r.raise_for_status()
        return r.json()

    def collect(self) -> Iterator[GaugeMetricFamily]:
        started = time.perf_counter()
        up = GaugeMetricFamily("well_up", "1 if the monitor's /api/status was read successfully")
        rth = GaugeMetricFamily("well_market_rth", "1 during US equity regular trading hours")
        rth.add_metric([], 1.0 if in_rth(self.clock()) else 0.0)
        try:
            status = self.fetch()
        except (httpx.HTTPError, ValueError) as err:
            log.warning("status fetch failed: %s", err)
            up.add_metric([], 0.0)
            yield from (up, rth, self._duration(started))
            return
        up.add_metric([], 1.0)
        yield from (up, rth)
        yield from self._recorder(status.get("recorder") or {})
        yield from self._streams(status.get("streams") or {})
        yield from self._misc(status)
        yield self._duration(started)

    @staticmethod
    def _duration(started: float) -> GaugeMetricFamily:
        g = GaugeMetricFamily("well_scrape_duration_seconds", "Time spent reading the monitor")
        g.add_metric([], time.perf_counter() - started)
        return g

    @staticmethod
    def _recorder(rec: dict) -> Iterator[GaugeMetricFamily]:
        running = GaugeMetricFamily("well_recorder_running", "1 if the recorder container is running")
        running.add_metric([], 1.0 if rec.get("state") == "running" else 0.0)
        yield running
        for key, name, doc in (
            ("uptimeSeconds", "well_recorder_uptime_seconds", "Recorder container uptime"),
            ("restartCount", "well_recorder_restart_count", "Recorder container restart count"),
        ):
            if isinstance(rec.get(key), int | float):
                g = GaugeMetricFamily(name, doc)
                g.add_metric([], float(rec[key]))
                yield g

    @staticmethod
    def _streams(streams: dict) -> Iterator[GaugeMetricFamily]:
        labels = ["symbol", "source"]
        age = GaugeMetricFamily("well_stream_age_seconds", "Seconds since the stream's last event", labels=labels)
        rows = GaugeMetricFamily("well_stream_rows_last_1m", "Rows written in the last minute", labels=labels)
        state = GaugeMetricFamily("well_stream_state", "1 for the stream's current state", labels=[*labels, "state"])
        entries = list(streams.get("perSymbol") or [])
        if streams.get("optionContracts"):
            entries.append({**streams["optionContracts"], "symbol": "option_contracts"})
        for s in entries:
            lv = [str(s.get("symbol", "")), str(s.get("source", ""))]
            if isinstance(s.get("ageSeconds"), int | float):
                age.add_metric(lv, float(s["ageSeconds"]))
            if isinstance(s.get("rowsLast1m"), int | float):
                rows.add_metric(lv, float(s["rowsLast1m"]))
            current = s.get("state") if s.get("state") in STATES else "unknown"
            for st in STATES:
                state.add_metric([*lv, st], 1.0 if st == current else 0.0)
        yield from (age, rows, state)

    @staticmethod
    def _misc(status: dict) -> Iterator[GaugeMetricFamily]:
        if isinstance(status.get("cacheAgeSeconds"), int | float):
            g = GaugeMetricFamily("well_monitor_cache_age_seconds", "Age of the monitor's own status cache")
            g.add_metric([], float(status["cacheAgeSeconds"]))
            yield g
        size = (status.get("storage") or {}).get("dbSizeBytes")
        if isinstance(size, int | float):
            g = GaugeMetricFamily("well_db_size_bytes", "Recorder database size")
            g.add_metric([], float(size))
            yield g
