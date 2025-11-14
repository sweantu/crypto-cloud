chmod +x run_clickhouse_init.sh

docker compose exec clickhouse clickhouse-client -u default --password 123456 --database testdb --query="SHOW TABLES;"

clickhouse_public_ip="18.142.254.168"
ssh -i ~/.ssh/sweantu ubuntu@${clickhouse_public_ip} "mkdir -p /home/ubuntu/clickhouse"
rsync -avz -e "ssh -i ~/.ssh/sweantu" ../clickhouse/ ubuntu@${clickhouse_public_ip}:/home/ubuntu/clickhouse/
ssh -i ~/.ssh/sweantu ubuntu@${clickhouse_public_ip}
docker exec clickhouse clickhouse-client --user default --password 123456 --database testdb   --query "SHOW TABLES;"
sudo tail -f /var/log/cloud-init-output.log