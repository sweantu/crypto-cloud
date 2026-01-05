resource "aws_db_subnet_group" "public" {
  name       = "${var.project_prefix}-public-db-subnet"
  subnet_ids = var.public_subnet_ids
}

resource "aws_security_group" "db_sg" {
  name   = "${var.project_prefix}-db-sg"
  vpc_id = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
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

resource "aws_db_instance" "airflow_db" {
  identifier             = "${var.project_prefix}-airflow-db"
  engine                 = "postgres"
  engine_version         = "15"
  instance_class         = "db.t4g.micro"
  allocated_storage      = 20
  db_name                = var.airflow_db_name
  username               = var.airflow_db_username
  password               = var.airflow_db_password
  publicly_accessible    = true
  skip_final_snapshot    = true
  multi_az               = false
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.public.name
}
