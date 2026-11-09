resource "github_repository" "this" {
  name         = var.repository
  description  = "GitOps platform for a live market-data recorder: k3s, Helm, ArgoCD, GitHub Actions, Prometheus SLOs with error budgets"
  visibility   = "public"
  topics       = ["gitops", "argocd", "kubernetes", "helm", "prometheus", "slo", "github-actions", "terraform", "dora-metrics"]
  has_issues   = true
  has_projects = false
  has_wiki     = false

  allow_merge_commit     = false
  allow_rebase_merge     = false
  allow_squash_merge     = true
  delete_branch_on_merge = true
  allow_auto_merge       = true # PRs merge themselves once every required check is green

  lifecycle { prevent_destroy = true }
}

# CI's deploy job pushes the image-tag commit with this key. It is the only actor allowed to
# bypass the ruleset, and only because that commit is generated after the same checks passed.
resource "tls_private_key" "deploy" {
  algorithm = "ED25519"
}

resource "github_repository_deploy_key" "ci" {
  repository = github_repository.this.name
  title      = "ci-gitops-tag-bump"
  key        = tls_private_key.deploy.public_key_openssh
  read_only  = false
}

resource "github_actions_secret" "deploy_key" {
  repository      = github_repository.this.name
  secret_name     = "DEPLOY_KEY"
  plaintext_value = tls_private_key.deploy.private_key_openssh
}

resource "github_repository_ruleset" "main" {
  name        = "main"
  repository  = github_repository.this.name
  target      = "branch"
  enforcement = "active"

  conditions {
    ref_name {
      include = ["~DEFAULT_BRANCH"]
      exclude = []
    }
  }

  bypass_actors {
    actor_type  = "DeployKey"
    bypass_mode = "always"
  }

  rules {
    deletion         = true
    non_fast_forward = true

    pull_request {
      required_approving_review_count   = 0 # single maintainer; the checks are the gate
      dismiss_stale_reviews_on_push     = true
      required_review_thread_resolution = true
    }

    required_status_checks {
      strict_required_status_checks_policy = true
      dynamic "required_check" {
        for_each = var.required_checks
        content {
          context = required_check.value
        }
      }
    }
  }
}

resource "github_repository_vulnerability_alerts" "this" {
  repository = github_repository.this.name
  enabled    = true
}
