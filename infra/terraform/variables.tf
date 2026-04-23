variable "project_name" {
  description = "Short project slug used for naming."
  type        = string
  default     = "utw"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "production"
}

variable "aws_region" {
  description = "AWS region for the stack."
  type        = string
}

variable "vpc_cidr" {
  description = "Primary VPC CIDR."
  type        = string
  default     = "10.40.0.0/16"
}

variable "availability_zone_count" {
  description = "Number of AZs to use."
  type        = number
  default     = 2
}

variable "backend_image_tag" {
  description = "ECR image tag for the backend image."
  type        = string
}

variable "frontend_image_tag" {
  description = "ECR image tag for the frontend image."
  type        = string
}

variable "domain_name" {
  description = "Primary public app domain, for example app.example.com."
  type        = string
}

variable "hosted_zone_name" {
  description = "Route53 hosted zone name used for DNS validation, for example example.com."
  type        = string
}

variable "api_desired_count" {
  description = "Desired number of backend ECS tasks."
  type        = number
  default     = 2
}

variable "frontend_desired_count" {
  description = "Desired number of frontend ECS tasks."
  type        = number
  default     = 2
}

variable "browser_worker_desired_count" {
  description = "Desired number of browser-agent worker ECS tasks."
  type        = number
  default     = 1
}

variable "api_task_cpu" {
  description = "Fargate CPU units for the backend task."
  type        = number
  default     = 1024
}

variable "api_task_memory" {
  description = "Fargate memory in MiB for the backend task."
  type        = number
  default     = 2048
}

variable "frontend_task_cpu" {
  description = "Fargate CPU units for the frontend task."
  type        = number
  default     = 512
}

variable "frontend_task_memory" {
  description = "Fargate memory in MiB for the frontend task."
  type        = number
  default     = 1024
}

variable "browser_worker_task_cpu" {
  description = "Fargate CPU units for the browser-agent worker task."
  type        = number
  default     = 1024
}

variable "browser_worker_task_memory" {
  description = "Fargate memory in MiB for the browser-agent worker task."
  type        = number
  default     = 2048
}

variable "api_min_capacity" {
  description = "Minimum autoscaling capacity for the backend ECS service."
  type        = number
  default     = 2
}

variable "api_max_capacity" {
  description = "Maximum autoscaling capacity for the backend ECS service."
  type        = number
  default     = 6
}

variable "frontend_min_capacity" {
  description = "Minimum autoscaling capacity for the frontend ECS service."
  type        = number
  default     = 2
}

variable "frontend_max_capacity" {
  description = "Maximum autoscaling capacity for the frontend ECS service."
  type        = number
  default     = 4
}

variable "browser_worker_min_capacity" {
  description = "Minimum autoscaling capacity for the browser-agent worker ECS service."
  type        = number
  default     = 1
}

variable "browser_worker_max_capacity" {
  description = "Maximum autoscaling capacity for the browser-agent worker ECS service."
  type        = number
  default     = 2
}

variable "rds_instance_class" {
  description = "RDS PostgreSQL instance class."
  type        = string
  default     = "db.t4g.medium"
}

variable "rds_engine_version" {
  description = "RDS PostgreSQL engine version. Keep this pinned deliberately per environment."
  type        = string
  default     = "16"
}

variable "rds_allocated_storage" {
  description = "Allocated RDS storage in GiB."
  type        = number
  default     = 100
}

variable "rds_max_allocated_storage" {
  description = "RDS autoscaling storage limit in GiB."
  type        = number
  default     = 500
}

variable "rds_backup_retention_period" {
  description = "Automated backup retention in days."
  type        = number
  default     = 14
}

variable "db_name" {
  description = "PostgreSQL database name."
  type        = string
  default     = "utw"
}

variable "db_username" {
  description = "PostgreSQL master username used by the application."
  type        = string
  default     = "utw_app"
}

variable "ses_sender_email" {
  description = "Verified SES sender address."
  type        = string
}

variable "ses_reply_to_email" {
  description = "Optional SES reply-to address."
  type        = string
  default     = ""
}

variable "ses_configuration_set" {
  description = "Optional SES configuration set."
  type        = string
  default     = ""
}

variable "ses_from_arn" {
  description = "Optional SES From identity ARN."
  type        = string
  default     = ""
}

variable "operator_email" {
  description = "Existing user email to promote with the bootstrap task."
  type        = string
}

variable "bedrock_model_id" {
  description = "Primary Bedrock model id."
  type        = string
  default     = "us.anthropic.claude-sonnet-4-20250514-v1:0"
}

variable "bedrock_fallback_model_id" {
  description = "Fallback Bedrock model id."
  type        = string
  default     = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
}

variable "ai_daily_request_budget" {
  description = "Hard daily AI request ceiling."
  type        = number
  default     = 500
}

variable "ai_daily_reserved_token_budget" {
  description = "Hard daily AI reserved token ceiling."
  type        = number
  default     = 2000000
}

variable "crawl_schedule_expression" {
  description = "EventBridge Scheduler expression for the crawl job."
  type        = string
  default     = "rate(30 minutes)"
}

variable "enrich_schedule_expression" {
  description = "EventBridge Scheduler expression for the enrichment job."
  type        = string
  default     = "rate(30 minutes)"
}

variable "match_schedule_expression" {
  description = "EventBridge Scheduler expression for the tender matching job."
  type        = string
  default     = "rate(30 minutes)"
}

variable "daily_briefs_schedule_expression" {
  description = "EventBridge Scheduler expression for daily briefs."
  type        = string
  default     = "cron(0 4 * * ? *)"
}

variable "instant_alerts_schedule_expression" {
  description = "EventBridge Scheduler expression for instant alerts."
  type        = string
  default     = "rate(10 minutes)"
}

variable "alarm_email_endpoint" {
  description = "Optional email endpoint subscribed to the SNS alarm topic."
  type        = string
  default     = ""
}

variable "rds_free_storage_alarm_bytes" {
  description = "Free storage threshold for the RDS low storage alarm."
  type        = number
  default     = 21474836480
}
