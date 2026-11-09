#!/usr/bin/env bash
# Creates the cluster, installs ArgoCD, and hands everything else to GitOps (gitops/bootstrap/root.yaml).
# Idempotent: safe to re-run.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=versions.env
source "$here/versions.env"
export PATH="$HOME/.local/bin:$PATH"

# Durable state lives outside the cluster so a teardown/rebuild keeps it (ADR 0006).
RACK_DATA_DIR="${RACK_DATA_DIR:-$HOME/k3d-rack-data}"
mkdir -p "$RACK_DATA_DIR/prometheus"

if ! k3d cluster list rack >/dev/null 2>&1; then
  k3d cluster create --config "$here/k3d.yaml" --volume "$RACK_DATA_DIR:/data@all"
fi
kubectl config use-context k3d-rack >/dev/null

helm repo add argo https://argoproj.github.io/argo-helm >/dev/null 2>&1 || true
helm repo update argo >/dev/null
helm upgrade --install argocd argo/argo-cd --version "$ARGOCD_CHART_VERSION" \
  --namespace argocd --create-namespace --values "$here/argocd-values.yaml" --wait --timeout 10m

# Grafana admin password: random, generated once, lives only in the cluster.
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f - >/dev/null
if ! kubectl -n monitoring get secret grafana-admin >/dev/null 2>&1; then
  kubectl -n monitoring create secret generic grafana-admin \
    --from-literal=admin-user=admin --from-literal=admin-password="$(openssl rand -base64 24)"
fi

kubectl apply -f "$here/../gitops/bootstrap/root.yaml"
echo "ArgoCD:  https://<host>:8441  admin / kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"
echo "Grafana: http://<host>:8442   admin / kubectl -n monitoring get secret grafana-admin -o jsonpath='{.data.admin-password}' | base64 -d"
