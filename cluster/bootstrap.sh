#!/usr/bin/env bash
# Creates the cluster, installs ArgoCD, and hands everything else to GitOps (gitops/bootstrap/root.yaml).
# Idempotent: safe to re-run.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=versions.env
source "$here/versions.env"
export PATH="$HOME/.local/bin:$PATH"

if ! k3d cluster list rack >/dev/null 2>&1; then
  k3d cluster create --config "$here/k3d.yaml"
fi
kubectl config use-context k3d-rack >/dev/null

helm repo add argo https://argoproj.github.io/argo-helm >/dev/null 2>&1 || true
helm repo update argo >/dev/null
helm upgrade --install argocd argo/argo-cd --version "$ARGOCD_CHART_VERSION" \
  --namespace argocd --create-namespace --values "$here/argocd-values.yaml" --wait --timeout 10m

kubectl apply -f "$here/../gitops/bootstrap/root.yaml"
echo "ArgoCD: https://<host>:8441  user admin, password:"
echo "  kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"
