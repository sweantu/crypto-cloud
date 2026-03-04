output "clickhouse_instance_id" {
  value = aws_instance.clickhouse.id
}

output "clickhouse_instance_public_ip" {
  value = aws_instance.clickhouse.public_ip
}
