"""Pure computation of delivery metrics from commits and workflow runs. No I/O here.

Definitions (this repo's conventions, see ADR 0007):
- A *deployment* is a commit on main whose message starts ``deploy: <app> sha-<12 hex>``: the CI
  job that writes the new image tag. ArgoCD applies it within its poll interval (<= 3 min), so
  deploy-commit time is a close upper bound on reaching production minus that lag.
- *Lead time* is from the source commit's author time to its deploy commit.
- A deployment *failed* if a later commit on main reverts its source commit (git's
  ``This reverts commit <sha>`` trailer).
- *Time to restore* is from a failed deployment to the next deployment after the revert.
"""

import re
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta

DEPLOY_RE = re.compile(r"^deploy: (?P<app>\S+) sha-(?P<sha>[0-9a-f]{7,40})\b")
REVERT_RE = re.compile(r"This reverts commit (?P<sha>[0-9a-f]{7,40})")


@dataclass(frozen=True)
class Commit:
    sha: str
    message: str
    authored: datetime
    committed: datetime


@dataclass(frozen=True)
class Run:
    conclusion: str | None
    started: datetime
    updated: datetime


@dataclass
class Deployment:
    app: str
    source_sha: str
    at: datetime
    lead_time: timedelta | None
    failed: bool = False
    restored_after: timedelta | None = None


@dataclass
class Report:
    window: timedelta
    deployments: list[Deployment] = field(default_factory=list)
    ci_by_conclusion: dict[str, int] = field(default_factory=dict)
    ci_durations: list[float] = field(default_factory=list)

    @property
    def deploy_count(self) -> int:
        return len(self.deployments)

    @property
    def deploys_per_day(self) -> float:
        return self.deploy_count / (self.window.total_seconds() / 86400)

    def lead_time_quantile(self, q: float) -> float | None:
        return _quantile([d.lead_time.total_seconds() for d in self.deployments if d.lead_time is not None], q)

    @property
    def change_failure_ratio(self) -> float | None:
        return sum(d.failed for d in self.deployments) / self.deploy_count if self.deployments else None

    def restore_quantile(self, q: float) -> float | None:
        return _quantile([d.restored_after.total_seconds() for d in self.deployments if d.restored_after], q)

    def ci_duration_quantile(self, q: float) -> float | None:
        return _quantile(self.ci_durations, q)


def _quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    return statistics.quantiles(sorted(values), n=100, method="inclusive")[round(q * 100) - 1]


def _lookup(commits_by_sha: dict[str, Commit], prefix: str) -> Commit | None:
    if prefix in commits_by_sha:
        return commits_by_sha[prefix]
    return next((c for s, c in commits_by_sha.items() if s.startswith(prefix)), None)


def compute(commits: list[Commit], runs: list[Run], now: datetime, window: timedelta) -> Report:
    since = now - window
    by_sha = {c.sha: c for c in commits}
    ordered = sorted(commits, key=lambda c: c.committed)
    reverts = [(c, m.group("sha")) for c in ordered if (m := REVERT_RE.search(c.message))]

    deploys: list[Deployment] = []
    for c in ordered:
        m = DEPLOY_RE.match(c.message)
        if not m:
            continue
        src = _lookup(by_sha, m.group("sha"))
        lead = c.committed - src.authored if src else None
        deploys.append(Deployment(m.group("app"), src.sha if src else m.group("sha"), c.committed, lead))

    def reverts_of(sha: str) -> Commit | None:
        return next((rc for rc, target in reverts if sha.startswith(target) or target.startswith(sha)), None)

    for d in deploys:
        revert = reverts_of(d.source_sha)
        if revert is None:
            continue
        d.failed = True
        fix = next((n for n in deploys if n.app == d.app and n.at >= revert.committed), None)
        if fix is not None:
            d.restored_after = fix.at - d.at

    report = Report(window=window, deployments=[d for d in deploys if d.at >= since])
    for r in runs:
        if r.started < since:
            continue
        key = r.conclusion or "in_progress"
        report.ci_by_conclusion[key] = report.ci_by_conclusion.get(key, 0) + 1
        if r.conclusion:
            report.ci_durations.append((r.updated - r.started).total_seconds())
    return report
