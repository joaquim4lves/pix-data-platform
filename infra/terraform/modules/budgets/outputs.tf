output "budget_name" {
  description = "Account-wide monthly cost budget."
  value       = aws_budgets_budget.monthly.name
}
