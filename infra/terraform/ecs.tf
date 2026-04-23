resource "aws_security_group" "alb" {
  name        = "${local.name_prefix}-alb"
  description = "Public ALB security group"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "api" {
  name        = "${local.name_prefix}-api"
  description = "Backend ECS security group"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "frontend" {
  name        = "${local.name_prefix}-frontend"
  description = "Frontend ECS security group"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "browser_worker" {
  name        = "${local.name_prefix}-browser-worker"
  description = "Browser-agent worker ECS security group"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "db" {
  name        = "${local.name_prefix}-db"
  description = "RDS PostgreSQL security group"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.api.id, aws_security_group.browser_worker.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/aws/ecs/${local.name_prefix}/api"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/aws/ecs/${local.name_prefix}/frontend"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "browser_worker" {
  name              = "/aws/ecs/${local.name_prefix}/browser-worker"
  retention_in_days = 30
}

resource "aws_ecs_cluster" "main" {
  name = "${local.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_lb" "main" {
  name               = substr("${local.name_prefix}-alb", 0, 32)
  load_balancer_type = "application"
  internal           = false
  security_groups    = [aws_security_group.alb.id]
  subnets            = [for subnet in aws_subnet.public : subnet.id]
}

resource "aws_lb_target_group" "api" {
  name        = substr("${local.name_prefix}-api", 0, 32)
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
    path                = "/health/ready"
    matcher             = "200"
  }
}

resource "aws_lb_target_group" "frontend" {
  name        = substr("${local.name_prefix}-frontend", 0, 32)
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
    path                = "/"
    matcher             = "200-399"
  }
}

resource "aws_acm_certificate" "app" {
  domain_name       = var.domain_name
  validation_method = "DNS"
}

resource "aws_route53_record" "cert_validation" {
  for_each = {
    for option in aws_acm_certificate.app.domain_validation_options :
    option.domain_name => {
      name  = option.resource_record_name
      type  = option.resource_record_type
      value = option.resource_record_value
    }
  }

  zone_id = data.aws_route53_zone.selected.zone_id
  name    = each.value.name
  type    = each.value.type
  ttl     = 60
  records = [each.value.value]
}

resource "aws_acm_certificate_validation" "app" {
  certificate_arn         = aws_acm_certificate.app.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"
  certificate_arn   = aws_acm_certificate_validation.app.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

resource "aws_lb_listener_rule" "api_paths" {
  for_each = local.backend_path_pattern_groups

  listener_arn = aws_lb_listener.https.arn
  priority     = 100 + tonumber(each.key)

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }

  condition {
    path_pattern {
      values = each.value
    }
  }
}

resource "aws_route53_record" "app" {
  zone_id = data.aws_route53_zone.selected.zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "${local.name_prefix}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = tostring(var.api_task_cpu)
  memory                   = tostring(var.api_task_memory)
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.backend_task.arn

  runtime_platform {
    cpu_architecture        = "X86_64"
    operating_system_family = "LINUX"
  }

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = "${aws_ecr_repository.backend.repository_url}:${var.backend_image_tag}"
      essential = true
      command   = ["/app/deploy/bin/run-api.sh"]
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
      environment = []
      secrets = concat(
        [
          for key, parameter in aws_ssm_parameter.backend : {
            name      = key
            valueFrom = parameter.arn
          }
        ],
        [
          {
            name      = "UTW_DATABASE_URL"
            valueFrom = aws_secretsmanager_secret.database_url.arn
          },
          {
            name      = "UTW_AUTH_SECRET_KEY"
            valueFrom = aws_secretsmanager_secret.auth_secret_key.arn
          },
          {
            name      = "UTW_OPERATOR_API_KEY"
            valueFrom = aws_secretsmanager_secret.operator_api_key.arn
          }
        ]
      )
    }
  ])
}

resource "aws_ecs_task_definition" "frontend" {
  family                   = "${local.name_prefix}-frontend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = tostring(var.frontend_task_cpu)
  memory                   = tostring(var.frontend_task_memory)
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.frontend_task.arn

  runtime_platform {
    cpu_architecture        = "X86_64"
    operating_system_family = "LINUX"
  }

  container_definitions = jsonencode([
    {
      name      = "frontend"
      image     = "${aws_ecr_repository.frontend.repository_url}:${var.frontend_image_tag}"
      essential = true
      portMappings = [
        {
          containerPort = 3000
          hostPort      = 3000
          protocol      = "tcp"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.frontend.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
      environment = []
      secrets = concat(
        [
          for key, parameter in aws_ssm_parameter.frontend : {
            name      = key
            valueFrom = parameter.arn
          }
        ],
        [
          {
            name      = "UTW_OPERATOR_API_KEY"
            valueFrom = aws_secretsmanager_secret.operator_api_key.arn
          }
        ]
      )
    }
  ])
}

resource "aws_ecs_task_definition" "browser_worker" {
  family                   = "${local.name_prefix}-browser-worker"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = tostring(var.browser_worker_task_cpu)
  memory                   = tostring(var.browser_worker_task_memory)
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.backend_task.arn

  runtime_platform {
    cpu_architecture        = "X86_64"
    operating_system_family = "LINUX"
  }

  container_definitions = jsonencode([
    {
      name      = "browser-worker"
      image     = "${aws_ecr_repository.backend.repository_url}:${var.backend_image_tag}"
      essential = true
      command   = ["/app/deploy/bin/run-browser-agent-worker.sh"]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.browser_worker.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
      environment = []
      secrets = concat(
        [
          for key, parameter in aws_ssm_parameter.backend : {
            name      = key
            valueFrom = parameter.arn
          }
        ],
        [
          {
            name      = "UTW_DATABASE_URL"
            valueFrom = aws_secretsmanager_secret.database_url.arn
          },
          {
            name      = "UTW_AUTH_SECRET_KEY"
            valueFrom = aws_secretsmanager_secret.auth_secret_key.arn
          },
          {
            name      = "UTW_OPERATOR_API_KEY"
            valueFrom = aws_secretsmanager_secret.operator_api_key.arn
          }
        ]
      )
    }
  ])
}

resource "aws_ecs_service" "api" {
  name                               = "${local.name_prefix}-api"
  cluster                            = aws_ecs_cluster.main.id
  task_definition                    = aws_ecs_task_definition.backend.arn
  desired_count                      = var.api_desired_count
  launch_type                        = "FARGATE"
  health_check_grace_period_seconds  = 60
  enable_execute_command             = true
  wait_for_steady_state              = false

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    assign_public_ip = false
    security_groups  = [aws_security_group.api.id]
    subnets          = [for subnet in aws_subnet.app_private : subnet.id]
  }

  load_balancer {
    container_name   = "backend"
    container_port   = 8000
    target_group_arn = aws_lb_target_group.api.arn
  }

  depends_on = [aws_lb_listener.https]
}

resource "aws_ecs_service" "frontend" {
  name                              = "${local.name_prefix}-frontend"
  cluster                           = aws_ecs_cluster.main.id
  task_definition                   = aws_ecs_task_definition.frontend.arn
  desired_count                     = var.frontend_desired_count
  launch_type                       = "FARGATE"
  health_check_grace_period_seconds = 60
  enable_execute_command            = true
  wait_for_steady_state             = false

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    assign_public_ip = false
    security_groups  = [aws_security_group.frontend.id]
    subnets          = [for subnet in aws_subnet.app_private : subnet.id]
  }

  load_balancer {
    container_name   = "frontend"
    container_port   = 3000
    target_group_arn = aws_lb_target_group.frontend.arn
  }

  depends_on = [aws_lb_listener.https]
}

resource "aws_appautoscaling_target" "api" {
  max_capacity       = var.api_max_capacity
  min_capacity       = var.api_min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "api_cpu" {
  name               = "${local.name_prefix}-api-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }

    target_value       = 60
    scale_in_cooldown  = 120
    scale_out_cooldown = 60
  }
}

resource "aws_ecs_service" "browser_worker" {
  name                              = "${local.name_prefix}-browser-worker"
  cluster                           = aws_ecs_cluster.main.id
  task_definition                   = aws_ecs_task_definition.browser_worker.arn
  desired_count                     = var.browser_worker_desired_count
  launch_type                       = "FARGATE"
  platform_version                  = "LATEST"
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  enable_execute_command            = true

  network_configuration {
    assign_public_ip = false
    security_groups  = [aws_security_group.browser_worker.id]
    subnets          = [for subnet in aws_subnet.app_private : subnet.id]
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
}

resource "aws_appautoscaling_target" "frontend" {
  max_capacity       = var.frontend_max_capacity
  min_capacity       = var.frontend_min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.frontend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "frontend_cpu" {
  name               = "${local.name_prefix}-frontend-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.frontend.resource_id
  scalable_dimension = aws_appautoscaling_target.frontend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.frontend.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }

    target_value       = 60
    scale_in_cooldown  = 120
    scale_out_cooldown = 60
  }
}

resource "aws_appautoscaling_target" "browser_worker" {
  max_capacity       = var.browser_worker_max_capacity
  min_capacity       = var.browser_worker_min_capacity
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.browser_worker.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "browser_worker_cpu" {
  name               = "${local.name_prefix}-browser-worker-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.browser_worker.resource_id
  scalable_dimension = aws_appautoscaling_target.browser_worker.scalable_dimension
  service_namespace  = aws_appautoscaling_target.browser_worker.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }

    target_value       = 70
    scale_in_cooldown  = 120
    scale_out_cooldown = 60
  }
}
