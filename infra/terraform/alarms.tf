resource "aws_sns_topic" "alerts" {
  name = "${local.name_prefix}-alerts"
}

resource "aws_sns_topic_subscription" "alerts_email" {
  count = trimspace(var.alarm_email_endpoint) == "" ? 0 : 1

  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alarm_email_endpoint
}

resource "aws_sqs_queue" "scheduler_dlq" {
  name                      = "${local.name_prefix}-scheduler-dlq"
  message_retention_seconds = 1209600
  visibility_timeout_seconds = 30
}

resource "aws_cloudwatch_metric_alarm" "api_unhealthy_hosts" {
  alarm_name          = "${local.name_prefix}-api-unhealthy-hosts"
  alarm_description   = "The backend target group has one or more unhealthy tasks behind the ALB."
  namespace           = "AWS/ApplicationELB"
  metric_name         = "UnHealthyHostCount"
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 2
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
    TargetGroup  = aws_lb_target_group.api.arn_suffix
  }
}

resource "aws_cloudwatch_metric_alarm" "frontend_unhealthy_hosts" {
  alarm_name          = "${local.name_prefix}-frontend-unhealthy-hosts"
  alarm_description   = "The frontend target group has one or more unhealthy tasks behind the ALB."
  namespace           = "AWS/ApplicationELB"
  metric_name         = "UnHealthyHostCount"
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 2
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    LoadBalancer = aws_lb.main.arn_suffix
    TargetGroup  = aws_lb_target_group.frontend.arn_suffix
  }
}

resource "aws_cloudwatch_metric_alarm" "api_running_task_count" {
  alarm_name          = "${local.name_prefix}-api-running-task-count"
  alarm_description   = "The backend ECS service has fallen below one running task."
  namespace           = "ECS/ContainerInsights"
  metric_name         = "RunningTaskCount"
  statistic           = "Minimum"
  period              = 60
  evaluation_periods  = 3
  threshold           = 1
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "breaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.api.name
  }
}

resource "aws_cloudwatch_metric_alarm" "frontend_running_task_count" {
  alarm_name          = "${local.name_prefix}-frontend-running-task-count"
  alarm_description   = "The frontend ECS service has fallen below one running task."
  namespace           = "ECS/ContainerInsights"
  metric_name         = "RunningTaskCount"
  statistic           = "Minimum"
  period              = 60
  evaluation_periods  = 3
  threshold           = 1
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "breaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.frontend.name
  }
}

resource "aws_cloudwatch_metric_alarm" "browser_worker_running_task_count" {
  alarm_name          = "${local.name_prefix}-browser-worker-running-task-count"
  alarm_description   = "The browser-agent worker ECS service has fallen below one running task."
  namespace           = "ECS/ContainerInsights"
  metric_name         = "RunningTaskCount"
  statistic           = "Minimum"
  period              = 60
  evaluation_periods  = 3
  threshold           = 1
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "breaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.browser_worker.name
  }
}

resource "aws_cloudwatch_metric_alarm" "scheduler_target_errors" {
  alarm_name          = "${local.name_prefix}-scheduler-target-errors"
  alarm_description   = "At least one scheduled ECS task invocation failed at the target API."
  namespace           = "AWS/Scheduler"
  metric_name         = "TargetErrorCount"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    ScheduleGroup = aws_scheduler_schedule_group.jobs.name
  }
}

resource "aws_cloudwatch_metric_alarm" "scheduler_invocation_dropped" {
  alarm_name          = "${local.name_prefix}-scheduler-invocation-dropped"
  alarm_description   = "At least one scheduled job exhausted retries and was dropped."
  namespace           = "AWS/Scheduler"
  metric_name         = "InvocationDroppedCount"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    ScheduleGroup = aws_scheduler_schedule_group.jobs.name
  }
}

resource "aws_cloudwatch_metric_alarm" "scheduler_dlq_visible_messages" {
  alarm_name          = "${local.name_prefix}-scheduler-dlq-visible-messages"
  alarm_description   = "The scheduler DLQ has messages waiting for operator investigation."
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    QueueName = aws_sqs_queue.scheduler_dlq.name
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_low_free_storage" {
  alarm_name          = "${local.name_prefix}-rds-low-free-storage"
  alarm_description   = "RDS free storage has fallen below the configured threshold."
  namespace           = "AWS/RDS"
  metric_name         = "FreeStorageSpace"
  statistic           = "Minimum"
  period              = 300
  evaluation_periods  = 2
  threshold           = var.rds_free_storage_alarm_bytes
  comparison_operator = "LessThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.identifier
  }
}
