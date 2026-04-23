resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "random_password" "auth_secret_key" {
  length  = 64
  special = false
}

resource "random_password" "operator_api_key" {
  length  = 48
  special = false
}

resource "random_id" "db_final_snapshot" {
  byte_length = 4
}

resource "aws_db_instance" "main" {
  identifier                      = "${local.name_prefix}-postgres"
  engine                          = "postgres"
  engine_version                  = var.rds_engine_version
  instance_class                  = var.rds_instance_class
  db_name                         = var.db_name
  username                        = var.db_username
  password                        = random_password.db_password.result
  allocated_storage               = var.rds_allocated_storage
  max_allocated_storage           = var.rds_max_allocated_storage
  storage_type                    = "gp3"
  storage_encrypted               = true
  multi_az                        = true
  backup_retention_period         = var.rds_backup_retention_period
  backup_window                   = "02:00-03:00"
  maintenance_window              = "sun:03:30-sun:04:30"
  auto_minor_version_upgrade      = true
  deletion_protection             = true
  copy_tags_to_snapshot           = true
  skip_final_snapshot             = false
  final_snapshot_identifier       = "${local.name_prefix}-final-${random_id.db_final_snapshot.hex}"
  publicly_accessible             = false
  performance_insights_enabled    = true
  monitoring_interval             = 60
  monitoring_role_arn             = aws_iam_role.rds_enhanced_monitoring.arn
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  db_subnet_group_name            = aws_db_subnet_group.main.name
  vpc_security_group_ids          = [aws_security_group.db.id]
}

resource "aws_secretsmanager_secret" "database_url" {
  name                    = "${local.parameter_prefix}/backend/database-url"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id     = aws_secretsmanager_secret.database_url.id
  secret_string = "postgresql+psycopg://${var.db_username}:${random_password.db_password.result}@${aws_db_instance.main.address}:5432/${var.db_name}"
}

resource "aws_secretsmanager_secret" "auth_secret_key" {
  name                    = "${local.parameter_prefix}/backend/auth-secret-key"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "auth_secret_key" {
  secret_id     = aws_secretsmanager_secret.auth_secret_key.id
  secret_string = random_password.auth_secret_key.result
}

resource "aws_secretsmanager_secret" "operator_api_key" {
  name                    = "${local.parameter_prefix}/shared/operator-api-key"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "operator_api_key" {
  secret_id     = aws_secretsmanager_secret.operator_api_key.id
  secret_string = random_password.operator_api_key.result
}

resource "aws_ssm_parameter" "backend" {
  for_each = merge(
    local.backend_environment,
    {
      for key, value in local.backend_optional_environment :
      key => value
      if trimspace(value) != ""
    }
  )

  name  = "${local.parameter_prefix}/backend/${lower(replace(each.key, "_", "-"))}"
  type  = "String"
  value = each.value
}

resource "aws_ssm_parameter" "frontend" {
  for_each = local.frontend_environment

  name  = "${local.parameter_prefix}/frontend/${lower(replace(each.key, "_", "-"))}"
  type  = "String"
  value = each.value
}
