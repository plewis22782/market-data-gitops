from datetime import UTC, datetime

import httpx

from delivery_metrics.github import GitHub

SINCE = datetime(2026, 11, 1, tzinfo=UTC)


def gh(handler):
    return GitHub("o/r", client=httpx.Client(base_url="https://api.github.com", transport=httpx.MockTransport(handler)))


def test_commits_paginate_and_parse():
    calls = []

    def handler(req):
        calls.append(dict(req.url.params))
        page = int(req.url.params["page"])
        n = 100 if page == 1 else 3
        body = [
            {"sha": f"{page}{i:039d}", "commit": {"message": "m", "author": {"date": "2026-11-02T10:00:00Z"},
                                                  "committer": {"date": "2026-11-02T10:05:00Z"}}}
            for i in range(n)
        ]
        return httpx.Response(200, json=body)

    commits = gh(handler).commits(SINCE)
    assert len(commits) == 103 and len(calls) == 2
    assert calls[0]["sha"] == "main" and calls[0]["per_page"] == "100"
    assert commits[0].committed == datetime(2026, 11, 2, 10, 5, tzinfo=UTC)


def test_runs_parse():
    body = {"workflow_runs": [{"conclusion": "success", "run_started_at": "2026-11-02T10:00:00Z",
                               "updated_at": "2026-11-02T10:02:00Z"}]}
    runs = gh(lambda req: httpx.Response(200, json=body)).runs(SINCE)
    assert runs[0].conclusion == "success" and (runs[0].updated - runs[0].started).seconds == 120
