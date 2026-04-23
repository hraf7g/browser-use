resource "aws_scheduler_schedule_group" "jobs" {
  name = "${local.name_prefix}-jobs"
}

resource "aws_scheduler_schedule" "job" {
  for_each = local.scheduler_jobs

  name       = "${local.name_prefix}-${replace(each.key, "_", "-")}"
  group_name = aws_scheduler_schedule_group.jobs.name

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = each.value.schedule_expression
  state               = "ENABLED"

  target {
    arn      = aws_ecs_cluster.main.arn
    role_arn = aws_iam_role.scheduler.arn

    ecs_parameters {
      launch_type         = "FARGATE"
      task_definition_arn = aws_ecs_task_definition.backend.arn
      task_count          = 1
      platform_version    = "LATEST"

      network_configuration {
        assign_public_ip = false
        security_groups  = [aws_security_group.api.id]
        subnets          = [for subnet in aws_subnet.app_private : subnet.id]
      }
    }

    dead_letter_config {
      arn = aws_sqs_queue.scheduler_dlq.arn
    }

    input = jsonencode({
      containerOverrides = [
        {
          name    = "backend"
          command = each.value.command
        }
      ]
    })

    retry_policy {
      maximum_event_age_in_seconds = 3600
      maximum_retry_attempts       = 3
    }
  }
}
