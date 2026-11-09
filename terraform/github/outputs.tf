output "ruleset_id" {
  value = github_repository_ruleset.main.ruleset_id
}

output "deploy_key_fingerprint" {
  value = tls_private_key.deploy.public_key_fingerprint_sha256
}
