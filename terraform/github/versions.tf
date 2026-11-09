terraform {
  required_version = ">= 1.9"
  required_providers {
    github = { source = "integrations/github", version = "~> 6.6" }
    tls    = { source = "hashicorp/tls", version = "~> 4.1" }
  }
  # Local state on purpose for a single-operator lab: it holds the deploy key, so it is
  # gitignored and kept 0600 on the operator host. See docs/adr/0008-terraform-for-github.md.
}

provider "github" {
  owner = var.owner
  # Token from the GITHUB_TOKEN environment variable; never in a file in this repo.
}
