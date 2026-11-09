# 8. Manage the GitHub side with Terraform; PRs and green checks gate main

Date: 2026-11-09 · Status: accepted

## Context
The path to production is only as safe as the rules on `main`. Clicking those rules into the
GitHub UI leaves no review trail and no way to rebuild them.

## Decision
`terraform/github` manages:
- repository settings (squash-only merges, delete merged branches, vulnerability alerts), adopted
  with an `import` block rather than recreated;
- a ruleset on the default branch: PR required, every CI job required and up to date, no
  force-push, no deletion;
- an ed25519 deploy key, stored as the `DEPLOY_KEY` Actions secret. It's the ruleset's only
  bypass actor, so CI's tag-bump commit (made after the same checks passed) can land on main.

State is local and gitignored: it holds the deploy key's private half. CI runs `terraform fmt`,
`init -backend=false` and `validate` on every PR; `apply` is a reviewed, manual step.

## Consequences
- No direct pushes to main, including from the maintainer. Every change is a PR.
- Losing the local state means re-importing the repo and ruleset, and rotating the deploy key
  (a new `apply` does both). A remote backend with locking is the upgrade once there's a second operator.
