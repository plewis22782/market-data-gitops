# terraform/github

The GitHub side of the platform as code: repository settings, the `main` ruleset (PR required,
all CI checks green, no force-push or deletion), and the deploy key CI uses for the GitOps tag bump.

```bash
export GITHUB_TOKEN=...            # repo-admin token, from the environment only
terraform init
terraform plan -out tfplan         # review, then
terraform apply tfplan
```

State is local and gitignored because it contains the deploy key's private half (ADR 0008).
CI runs `terraform fmt -check` and `terraform validate` on every PR.
