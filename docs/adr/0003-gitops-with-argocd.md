# 3. GitOps with ArgoCD; CI writes the image tag, never deploys

Date: 2026-11-09 · Status: accepted

## Context
Deploys should be push-button and reversible, and the cluster's state should be readable from
git. A CI job running `helm upgrade` against the cluster needs cluster credentials in CI and
leaves no record of what is supposed to be running.

## Decision
- ArgoCD runs an app of apps (`gitops/bootstrap/root.yaml` → `gitops/apps/`), automated sync with
  prune and self-heal.
- Images are tagged with the commit SHA. On merge to `main`, CI pushes the image and commits the
  new tag to `gitops/values/freshness-exporter.yaml`. ArgoCD deploys that commit.
- Third-party charts (kube-prometheus-stack, argo-cd) are pinned to exact versions.

## Consequences
- Every deploy is a commit; rollback is `git revert`. Drift is corrected by self-heal.
- CI holds a registry token but no cluster credentials.
- The tag-bump commit must not retrigger a build (`paths-ignore: gitops/values/**`).
- ArgoCD itself is installed by `cluster/bootstrap.sh`, not by GitOps. Making ArgoCD manage itself is a later step.
