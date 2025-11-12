variable "project_prefix" { type = string }
variable "environment" { type = string }
variable "project" { type = string }

variable "vpc_id" { type = string }
variable "subnet_id" { type = string }

variable "instance_type" {
  type    = string
  default = "t3.medium"
}

variable "key_name" {
  type    = string
  default = "sweantu"
}

variable "ami_id" {
  type        = string
  description = "Ubuntu 22.04 AMI"
  default     = "ami-0827b3068f1548bf6"
}

resource "aws_security_group" "clickhouse_sg" {
  name        = "${var.project_prefix}-clickhouse-sg"
  description = "Allow ClickHouse HTTP + native ports"
  vpc_id      = var.vpc_id

  ingress {
    description = "ClickHouse HTTP"
    from_port   = 8123
    to_port     = 8123
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Restrict later to your VPC or Grafana
  }

  ingress {
    description = "ClickHouse native TCP"
    from_port   = 9000
    to_port     = 9000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_prefix}-clickhouse-sg"
    Environment = var.environment
    Project     = var.project
  }
}

resource "aws_instance" "clickhouse" {
  ami                         = var.ami_id
  instance_type               = var.instance_type
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [aws_security_group.clickhouse_sg.id]
  key_name                    = var.key_name
  associate_public_ip_address = true

  root_block_device {
    volume_size = 50
    volume_type = "gp3"
  }

  user_data = <<-EOF
    #!/bin/bash
    set -euxo pipefail

    # --- Install Docker ---
    apt update -y
    apt install -y ca-certificates curl gnupg lsb-release
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
      https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
      | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt update -y
    apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    systemctl enable docker
    systemctl start docker

    # --- Allow 'ubuntu' user to use Docker without sudo ---
    usermod -aG docker ubuntu
    newgrp docker || true  # refresh group (won't persist in user_data, but ensures group exists)

    # Wait for Docker daemon to be ready
    sleep 10

    # --- Start ClickHouse ---
    docker run -d --name clickhouse \
      -p 8123:8123 -p 9000:9000 \
      -e CLICKHOUSE_DB=testdb \
      -e CLICKHOUSE_USER=default \
      -e CLICKHOUSE_PASSWORD=123456 \
      -v /var/lib/clickhouse:/var/lib/clickhouse \
      clickhouse/clickhouse-server:25.8.10.7

    # Auto-restart on reboot
    docker update --restart=always clickhouse

    # --- Health Check ---
    echo "Waiting for ClickHouse to start..."
    sleep 15

    if docker exec clickhouse clickhouse-client --query "SELECT version();" >/tmp/ch_version.txt 2>&1; then
        echo "✅ ClickHouse started successfully. Version:"
        cat /tmp/ch_version.txt
    else
        echo "❌ ClickHouse failed to start. Logs:"
        docker logs clickhouse | tail -n 50
    fi
  EOF

  tags = {
    Name        = "${var.project_prefix}-clickhouse"
    Environment = var.environment
    Project     = var.project
  }
}

output "clickhouse_public_ip" {
  description = "Public IP of the ClickHouse instance"
  value       = aws_instance.clickhouse.public_ip
}
