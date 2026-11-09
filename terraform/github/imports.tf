# The repository existed before Terraform; adopt it instead of recreating it.
import {
  to = github_repository.this
  id = "market-data-gitops"
}
