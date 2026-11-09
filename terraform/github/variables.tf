variable "owner" {
  type    = string
  default = "plewis22782"
}

variable "repository" {
  type    = string
  default = "market-data-gitops"
}

variable "required_checks" {
  description = "CI job names that must pass before anything merges to main."
  type        = list(string)
  default = [
    "python (freshness-exporter)",
    "python (delivery-metrics)",
    "rules",
    "manifests",
    "terraform",
    "image (freshness-exporter)",
    "image (delivery-metrics)",
  ]
}
