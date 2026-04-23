resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
}

resource "aws_subnet" "public" {
  for_each = {
    for index, az in local.azs :
    az => {
      az   = az
      cidr = local.public_subnet_cidrs[index]
    }
  }

  vpc_id                  = aws_vpc.main.id
  availability_zone       = each.value.az
  cidr_block              = each.value.cidr
  map_public_ip_on_launch = true
}

resource "aws_subnet" "app_private" {
  for_each = {
    for index, az in local.azs :
    az => {
      az   = az
      cidr = local.app_private_subnet_cidrs[index]
    }
  }

  vpc_id            = aws_vpc.main.id
  availability_zone = each.value.az
  cidr_block        = each.value.cidr
}

resource "aws_subnet" "db_private" {
  for_each = {
    for index, az in local.azs :
    az => {
      az   = az
      cidr = local.db_private_subnet_cidrs[index]
    }
  }

  vpc_id            = aws_vpc.main.id
  availability_zone = each.value.az
  cidr_block        = each.value.cidr
}

resource "aws_eip" "nat" {
  for_each = aws_subnet.public

  domain = "vpc"
}

resource "aws_nat_gateway" "main" {
  for_each = aws_subnet.public

  allocation_id = aws_eip.nat[each.key].id
  subnet_id     = each.value.id

  depends_on = [aws_internet_gateway.main]
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
}

resource "aws_route_table_association" "public" {
  for_each = aws_subnet.public

  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "app_private" {
  for_each = aws_subnet.app_private

  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[each.key].id
  }
}

resource "aws_route_table_association" "app_private" {
  for_each = aws_subnet.app_private

  subnet_id      = each.value.id
  route_table_id = aws_route_table.app_private[each.key].id
}

resource "aws_route_table" "db_private" {
  vpc_id = aws_vpc.main.id
}

resource "aws_route_table_association" "db_private" {
  for_each = aws_subnet.db_private

  subnet_id      = each.value.id
  route_table_id = aws_route_table.db_private.id
}

resource "aws_db_subnet_group" "main" {
  name       = "${local.name_prefix}-db"
  subnet_ids = [for subnet in aws_subnet.db_private : subnet.id]
}
