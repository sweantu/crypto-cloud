
resource "aws_security_group" "clickhouse_sg" {
  name   = "${var.project_prefix}-clickhouse-sg"
  vpc_id = var.vpc_id

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
}

resource "aws_instance" "clickhouse" {
  ami                         = var.clickhouse_ami_id
  instance_type               = var.clickhouse_instance_type
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [aws_security_group.clickhouse_sg.id]
  key_name                    = var.key_name
  associate_public_ip_address = true

  root_block_device {
    volume_size = 50
    volume_type = "gp3"
  }

  user_data = <<-EOF
#!/usr/bin/env bash
set -euxo pipefail

# --- Install prerequisites ---
apt update -y
apt install -y ca-certificates curl gnupg lsb-release

install -m 0755 -d /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    gpg --dearmor -o /etc/apt/keyrings/docker.gpg

chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt update -y
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable docker
systemctl start docker

usermod -aG docker ubuntu

sleep 30

docker run -d --name clickhouse \
  -p 8123:8123 -p 9000:9000 \
  -e CLICKHOUSE_DB="${var.clickhouse_db}" \
  -e CLICKHOUSE_USER="${var.clickhouse_user}" \
  -e CLICKHOUSE_PASSWORD="${var.clickhouse_password}" \
  -v /var/lib/clickhouse:/var/lib/clickhouse \
  clickhouse/clickhouse-server:25.5.1

docker update --restart=always clickhouse

echo "Waiting for ClickHouse..."
sleep 30

docker exec clickhouse clickhouse-client --query "SELECT version();" >/tmp/ch_version.txt 2>&1 || \
  docker logs clickhouse | tail -n 50

EOF

  tags = {
    Name = "${var.project_prefix}-clickhouse-instance"
  }
}
