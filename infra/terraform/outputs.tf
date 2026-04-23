output "alb_dns_name" {
  description = "Public ALB DNS name."
  value       = aws_lb.main.dns_name
}

output "app_url" {
  description = "Primary customer-facing application URL."
  value       = "https://${var.domain_name}"
}

output "backend_ecr_repository_url" {
  description = "Backend image repository URL."
  value       = aws_ecr_repository.backend.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name."
  value       = aws_ecs_cluster.main.name
}

output "api_service_name" {
  description = "Backend ECS service name."
  value       = aws_ecs_service.api.name
}

output "frontend_service_name" {
  description = "Frontend ECS service name."
  value       = aws_ecs_service.frontend.name
}

output "browser_worker_service_name" {
  description = "Browser-agent worker ECS service name."
  value       = aws_ecs_service.browser_worker.name
}

output "backend_task_definition_arn" {
  description = "Backend task definition ARN."
  value       = aws_ecs_task_definition.backend.arn
}

output "frontend_task_definition_arn" {
  description = "Frontend task definition ARN."
  value       = aws_ecs_task_definition.frontend.arn
}

output "browser_worker_task_definition_arn" {
  description = "Browser-agent worker task definition ARN."
  value       = aws_ecs_task_definition.browser_worker.arn
}

output "app_private_subnet_ids" {
  description = "Private application subnet ids for one-off ECS tasks."
  value       = [for subnet in aws_subnet.app_private : subnet.id]
}

output "backend_security_group_id" {
  description = "Backend ECS security group id for one-off ECS tasks."
  value       = aws_security_group.api.id
}

output "frontend_ecr_repository_url" {
  description = "Frontend image repository URL."
  value       = aws_ecr_repository.frontend.repository_url
}

output "alarm_sns_topic_arn" {
  description = "SNS topic ARN used for operational alarms."
  value       = aws_sns_topic.alerts.arn
}

output "scheduler_dlq_url" {
  description = "SQS URL for the scheduler dead-letter queue."
  value       = aws_sqs_queue.scheduler_dlq.id
}

output "operator_api_key_secret_arn" {
  description = "Secrets Manager ARN containing the operator API key."
  value       = aws_secretsmanager_secret.operator_api_key.arn
}

output "database_url_secret_arn" {
  description = "Secrets Manager ARN containing the application database URL."
  value       = aws_secretsmanager_secret.database_url.arn
}

output "bootstrap_promote_operator_command" {
  description = "Command override to run after the first user signs up."
  value       = ["/app/.venv/bin/python", "-m", "src.operator.promote_operator_user"]
}

output "bootstrap_migrate_command" {
  description = "One-off command override to apply database migrations."
  value       = ["/app/deploy/bin/run-db-migrate.sh"]
}

output "bootstrap_seed_command" {
  description = "One-off command override to seed monitored sources."
  value       = ["/app/deploy/bin/run-seed-sources.sh"]
}
