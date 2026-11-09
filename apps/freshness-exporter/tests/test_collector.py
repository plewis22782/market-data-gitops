import json
from datetime import UTC, datetime
from pathlib import Path

import httpx

from freshness_exporter.collector import StatusCollector

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "status.json").read_text())
RTH = datetime(2026, 11, 9, 17, 0, tzinfo=UTC)


def collector(handler):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return StatusCollector("http://monitor:8091/", client=client, clock=lambda: RTH)


def key(name, **labels):
    return (name, tuple(sorted(labels.items())))


def samples(c):
    out = {}
    for fam in c.collect():
        for s in fam.samples:
            out[(s.name, tuple(sorted(s.labels.items())))] = s.value
    return out


def test_happy_path():
    seen = []

    def handler(req):
        seen.append(str(req.url))
        return httpx.Response(200, json=FIXTURE)

    got = samples(collector(handler))
    assert seen == ["http://monitor:8091/api/status"]
    assert got[("well_up", ())] == 1
    assert got[("well_market_rth", ())] == 1
    assert got[("well_recorder_running", ())] == 1
    spx = {"source": "recorder", "symbol": "SPX"}
    assert got[key("well_stream_age_seconds", **spx)] == FIXTURE["streams"]["perSymbol"][0]["ageSeconds"]
    assert got[key("well_stream_state", **spx, state="fresh")] == 1
    assert got[key("well_stream_state", **spx, state="dark")] == 0
    assert key("well_stream_rows_last_1m", source="recorder", symbol="option_contracts") in got


def test_monitor_down_reports_up_zero_and_still_rth():
    def handler(req):
        raise httpx.ConnectError("refused", request=req)

    got = samples(collector(handler))
    assert got[("well_up", ())] == 0
    assert got[("well_market_rth", ())] == 1
    assert not any(k[0] == "well_stream_age_seconds" for k in got)


def test_http_500_is_down():
    got = samples(collector(lambda req: httpx.Response(500, json={"error": "internal error"})))
    assert got[("well_up", ())] == 0


def test_non_json_is_down():
    got = samples(collector(lambda req: httpx.Response(200, text="<html>")))
    assert got[("well_up", ())] == 0


def test_unknown_state_and_missing_fields():
    body = {"recorder": {"state": "exited"}, "streams": {"perSymbol": [{"symbol": "SPX", "state": "weird"}]}}
    got = samples(collector(lambda req: httpx.Response(200, json=body)))
    assert got[("well_recorder_running", ())] == 0
    assert got[key("well_stream_state", source="", symbol="SPX", state="unknown")] == 1
