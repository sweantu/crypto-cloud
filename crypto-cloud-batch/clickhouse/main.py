from clickhouse_connect import get_client

client = get_client(
    host="localhost",
    port=8123,
    username="default",
    password="123456",
    database="testdb",
)

client.command("""
CREATE TABLE IF NOT EXISTS testdb.metrics (
    id UInt32,
    metric Float32
) ENGINE = MergeTree() ORDER BY id
""")

client.insert("testdb.metrics", [(1, 0.5), (2, 0.8)], column_names=["id", "metric"])

rows = client.query("SELECT * FROM testdb.metrics").result_rows
print(rows)
