"""Minimal GitHub REST client: main-branch commits and push-triggered workflow runs since a date."""

from datetime import datetime

import httpx

from .dora import Commit, Run

API = "https://api.github.com"


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


class GitHub:
    def __init__(self, repo: str, token: str | None = None, client: httpx.Client | None = None, max_pages: int = 5):
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.repo = repo
        self.client = client or httpx.Client(base_url=API, headers=headers, timeout=20)
        self.max_pages = max_pages

    def _pages(self, path: str, params: dict, key: str | None = None) -> list[dict]:
        out: list[dict] = []
        for page in range(1, self.max_pages + 1):
            r = self.client.get(path, params={**params, "per_page": 100, "page": page})
            r.raise_for_status()
            items = r.json()[key] if key else r.json()
            out.extend(items)
            if len(items) < 100:
                break
        return out

    def commits(self, since: datetime, branch: str = "main") -> list[Commit]:
        raw = self._pages(f"/repos/{self.repo}/commits", {"sha": branch, "since": since.isoformat()})
        return [
            Commit(
                sha=c["sha"],
                message=c["commit"]["message"],
                authored=_ts(c["commit"]["author"]["date"]),
                committed=_ts(c["commit"]["committer"]["date"]),
            )
            for c in raw
        ]

    def runs(self, since: datetime, branch: str = "main") -> list[Run]:
        params = {"branch": branch, "event": "push", "created": f">={since.date().isoformat()}"}
        raw = self._pages(f"/repos/{self.repo}/actions/runs", params, key="workflow_runs")
        return [
            Run(conclusion=r.get("conclusion"), started=_ts(r["run_started_at"]), updated=_ts(r["updated_at"]))
            for r in raw
        ]
