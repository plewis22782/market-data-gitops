# 7. Measure delivery (DORA) from the repo's own history

Date: 2026-11-09 · Status: accepted

## Context
"Improves how quickly and safely engineers ship" needs numbers, not impressions. In a GitOps repo,
every production change is already a commit, so git history is the deployment log.

## Decision
`apps/delivery-metrics` reads main-branch commits and push-triggered workflow runs from the GitHub
API every 10 minutes and exports, over a 30-day window:

| Metric | Definition here |
|---|---|
| Deploy frequency | `deploy: <app> sha-<commit>` commits per day (the CI tag bump) |
| Lead time | source commit's author time → its deploy commit (p50, p90) |
| Change failure rate | share of deploys whose source commit is later reverted (`This reverts commit <sha>`) |
| Time to restore | failed deploy → the next deploy after the revert (p50) |
| CI health | main-branch runs by conclusion, run duration p50/p90 |

Pure computation lives in `dora.py` with unit tests; the GitHub client is tested against a mock transport.

## Consequences
- Deploy time is when CI committed the tag; ArgoCD applies it within its poll interval (≤ 3 min).
- Squash merges set the author time at merge, so lead time measures merge → production, not
  first commit → production. Measuring from the first PR commit needs the PR API (later).
- Failures are only counted when they're reverted. A forward fix isn't detected. The revert
  convention is the cheapest honest signal; incident-linked failures would be better.
- Unauthenticated API calls (~2–4 per refresh) fit the 60/h limit; a token secret is optional.
