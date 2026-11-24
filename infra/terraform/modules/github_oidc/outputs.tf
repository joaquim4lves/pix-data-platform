output "deploy_role_arn" {
  description = "Role ARN to store as the GitHub variable AWS_DEPLOY_ROLE_ARN."
  value       = aws_iam_role.deploy.arn
}

output "deploy_role_name" {
  description = "Deploy role name."
  value       = aws_iam_role.deploy.name
}

output "oidc_provider_arn" {
  description = "GitHub OIDC provider ARN, created or supplied."
  value       = local.oidc_arn
}
