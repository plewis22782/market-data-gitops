#!/usr/bin/env bash
# Installs k3d, kubectl and helm into ~/.local/bin (no sudo), checksum-verified.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=versions.env
source "$here/versions.env"
bin="$HOME/.local/bin"; mkdir -p "$bin"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT

fetch() { curl -fsSL --retry 3 -o "$1" "$2"; }

# kubectl: sha256 published next to the binary
fetch "$tmp/kubectl" "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl"
fetch "$tmp/kubectl.sha256" "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl.sha256"
echo "$(cat "$tmp/kubectl.sha256")  $tmp/kubectl" | sha256sum -c -
install -m 0755 "$tmp/kubectl" "$bin/kubectl"

# helm: tarball + .sha256sum
fetch "$tmp/helm.tgz" "https://get.helm.sh/helm-${HELM_VERSION}-linux-amd64.tar.gz"
fetch "$tmp/helm.sha" "https://get.helm.sh/helm-${HELM_VERSION}-linux-amd64.tar.gz.sha256sum"
(cd "$tmp" && echo "$(cut -d' ' -f1 helm.sha)  helm.tgz" | sha256sum -c -)
tar -xzf "$tmp/helm.tgz" -C "$tmp" linux-amd64/helm
install -m 0755 "$tmp/linux-amd64/helm" "$bin/helm"

# k3d: release checksums.txt
fetch "$tmp/k3d" "https://github.com/k3d-io/k3d/releases/download/${K3D_VERSION}/k3d-linux-amd64"
fetch "$tmp/k3d.sums" "https://github.com/k3d-io/k3d/releases/download/${K3D_VERSION}/checksums.txt"
(cd "$tmp" && grep ' k3d-linux-amd64$' k3d.sums | sed 's/k3d-linux-amd64/k3d/' | sha256sum -c -)
install -m 0755 "$tmp/k3d" "$bin/k3d"

"$bin/kubectl" version --client=true | head -1
"$bin/helm" version --short
"$bin/k3d" version | head -1
