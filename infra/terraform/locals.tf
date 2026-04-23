data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

data "aws_route53_zone" "selected" {
  name         = var.hosted_zone_name
  private_zone = false
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  azs         = slice(data.aws_availability_zones.available.names, 0, var.availability_zone_count)

  public_subnet_cidrs = [
    for index in range(length(local.azs)) :
    cidrsubnet(var.vpc_cidr, 8, index)
  ]

  app_private_subnet_cidrs = [
    for index in range(length(local.azs)) :
    cidrsubnet(var.vpc_cidr, 8, index + 10)
  ]

  db_private_subnet_cidrs = [
    for index in range(length(local.azs)) :
    cidrsubnet(var.vpc_cidr, 8, index + 20)
  ]

  backend_path_patterns = [
    "/auth*",
    "/me*",
    "/activity*",
    "/keyword-profile*",
    "/notification-settings*",
    "/tenders*",
    "/operator*",
    "/health*",
    "/openapi.json",
    "/docs*",
    "/redoc*",
  ]

  backend_path_pattern_groups = {
    for index, patterns in chunklist(local.backend_path_patterns, 5) :
    index => patterns
  }

  parameter_prefix = "/${var.project_name}/${var.environment}"

  backend_environment = {
    UTW_ENVIRONMENT                          = "production"
    UTW_DEBUG                                = "false"
    UTW_HOST                                 = "0.0.0.0"
    UTW_PORT                                 = "8000"
    UTW_AUTH_ISSUER                          = "utw-api"
    UTW_AUTH_AUDIENCE                        = "utw-users"
    UTW_AUTH_ACCESS_TOKEN_TTL_MINUTES        = "60"
    UTW_AUTH_COOKIE_NAME                     = "utw_access_token"
    UTW_AUTH_COOKIE_PATH                     = "/"
    UTW_AUTH_COOKIE_SAME_SITE                = "lax"
    UTW_AUTH_COOKIE_SECURE                   = "true"
    UTW_PASSWORD_RESET_TOKEN_TTL_MINUTES     = "60"
    UTW_FRONTEND_BASE_URL                    = "https://${var.domain_name}"
    UTW_CORS_ALLOW_ORIGINS                   = "https://${var.domain_name}"
    UTW_EMAIL_DELIVERY_BACKEND               = "ses"
    UTW_EMAIL_SENDER                         = var.ses_sender_email
    UTW_AWS_REGION                           = var.aws_region
    UTW_AI_PROVIDER                          = "bedrock_anthropic"
    UTW_AI_MODEL                             = var.bedrock_model_id
    UTW_AI_FALLBACK_MODEL                    = var.bedrock_fallback_model_id
    UTW_AI_BEDROCK_USE_AMBIENT_CREDENTIALS   = "true"
    UTW_AI_MAX_TOKENS                        = "4096"
    UTW_AI_TEMPERATURE                       = "0.0"
    UTW_AI_SUMMARY_BATCH_SIZE                = "25"
    UTW_AI_SUMMARY_MAX_ATTEMPTS              = "3"
    UTW_AI_DAILY_REQUEST_BUDGET              = tostring(var.ai_daily_request_budget)
    UTW_AI_DAILY_RESERVED_TOKEN_BUDGET       = tostring(var.ai_daily_reserved_token_budget)
    UTW_BROWSER_AGENT_ENABLED                = "true"
    UTW_BROWSER_AGENT_DEFAULT_MAX_STEPS      = "25"
    UTW_BROWSER_AGENT_STEP_TIMEOUT_SECONDS   = "180"
    UTW_BROWSER_AGENT_LLM_TIMEOUT_SECONDS    = "90"
    UTW_BROWSER_AGENT_MAX_CONCURRENT_RUNS_PER_USER = "1"
    UTW_BROWSER_AGENT_MAX_QUEUED_RUNS_PER_USER     = "3"
    UTW_BROWSER_AGENT_MAX_GLOBAL_RUNNING_RUNS      = tostring(var.browser_worker_max_capacity)
    UTW_BROWSER_AGENT_WORKER_POLL_SECONDS          = "10"
    UTW_BROWSER_AGENT_WORKER_STALE_HEARTBEAT_SECONDS = "900"
    BROWSER_USE_REQUIRE_EXPLICIT_LLM         = "true"
    DEFAULT_LLM                              = "bedrock_anthropic:${var.bedrock_model_id}"
    BROWSER_USE_AWS_REGION                   = var.aws_region
  }

  backend_optional_environment = {
    UTW_EMAIL_REPLY_TO              = var.ses_reply_to_email
    UTW_EMAIL_SES_CONFIGURATION_SET = var.ses_configuration_set
    UTW_EMAIL_SES_FROM_ARN          = var.ses_from_arn
    UTW_OPERATOR_EMAIL              = var.operator_email
  }

  frontend_environment = {
    NODE_ENV                     = "production"
    PORT                         = "3000"
    HOSTNAME                     = "0.0.0.0"
    NEXT_PUBLIC_API_URL          = "https://${var.domain_name}"
    NEXT_PUBLIC_AUTH_COOKIE_NAME = local.backend_environment.UTW_AUTH_COOKIE_NAME
  }

  scheduler_jobs = {
    run_all_sources = {
      schedule_expression = var.crawl_schedule_expression
      command             = ["/app/deploy/bin/run-all-sources.sh"]
    }
    enrich_recent = {
      schedule_expression = var.enrich_schedule_expression
      command             = ["/app/deploy/bin/run-enrich-recent.sh"]
    }
    match_recent = {
      schedule_expression = var.match_schedule_expression
      command             = ["/app/deploy/bin/run-match-recent.sh"]
    }
    send_daily_briefs = {
      schedule_expression = var.daily_briefs_schedule_expression
      command             = ["/app/deploy/bin/run-send-pending-daily-briefs.sh"]
    }
    send_instant_alerts = {
      schedule_expression = var.instant_alerts_schedule_expression
      command             = ["/app/deploy/bin/run-send-pending-instant-alerts.sh"]
    }
  }
}
