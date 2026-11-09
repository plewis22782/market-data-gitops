from datetime import UTC, datetime, timedelta

from delivery_metrics.dora import Commit, Run, compute

T0 = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)
NOW = T0 + timedelta(days=10)
W = timedelta(days=30)


def c(sha, msg, at, authored=None):
    return Commit(sha=sha, message=msg, authored=authored or at, committed=at)


def h(n):
    return T0 + timedelta(hours=n)


def test_lead_time_and_frequency():
    commits = [
        c("a" * 40, "feat: x", h(0), authored=h(-2)),
        c("b" * 40, "deploy: freshness-exporter sha-" + "a" * 12, h(0.25)),
        c("c" * 40, "fix: y", h(5)),
        c("d" * 40, "deploy: freshness-exporter sha-" + "c" * 12, h(5.5)),
    ]
    r = compute(commits, [], NOW, W)
    assert r.deploy_count == 2
    assert r.deploys_per_day == 2 / 30
    assert sorted(d.lead_time.total_seconds() for d in r.deployments) == [1800, 8100]
    assert r.change_failure_ratio == 0
    assert r.restore_quantile(0.5) is None


def test_revert_marks_failure_and_time_to_restore():
    bad = "e" * 40
    commits = [
        c(bad, "feat: risky", h(0)),
        c("f" * 40, "deploy: freshness-exporter sha-" + bad[:12], h(0.2)),
        c("1" * 40, f'Revert "feat: risky"\n\nThis reverts commit {bad}.', h(1)),
        c("2" * 40, "deploy: freshness-exporter sha-" + "1" * 12, h(1.2)),
    ]
    r = compute(commits, [], NOW, W)
    failed = [d for d in r.deployments if d.failed]
    assert len(failed) == 1 and failed[0].source_sha == bad
    assert r.change_failure_ratio == 0.5
    assert r.restore_quantile(0.5) == 3600  # 0.2 h -> 1.2 h


def test_window_excludes_old_deploys_but_still_finds_their_sources():
    old_src = c("3" * 40, "feat: old", NOW - timedelta(days=40))
    commits = [old_src, c("4" * 40, "deploy: freshness-exporter sha-" + "3" * 12, NOW - timedelta(days=29))]
    r = compute(commits, [], NOW, W)
    assert r.deploy_count == 1
    assert r.deployments[0].lead_time == timedelta(days=11)


def test_unknown_source_sha_has_no_lead_time():
    r = compute([c("5" * 40, "deploy: freshness-exporter sha-abcdef123456", h(1))], [], NOW, W)
    assert r.deploy_count == 1 and r.deployments[0].lead_time is None


def test_ci_runs():
    runs = [
        Run("success", h(0), h(0) + timedelta(seconds=90)),
        Run("failure", h(1), h(1) + timedelta(seconds=30)),
        Run(None, h(2), h(2)),
        Run("success", NOW - timedelta(days=31), NOW - timedelta(days=31)),
    ]
    r = compute([], runs, NOW, W)
    assert r.ci_by_conclusion == {"success": 1, "failure": 1, "in_progress": 1}
    assert sorted(r.ci_durations) == [30, 90]
    assert r.deploy_count == 0 and r.change_failure_ratio is None
