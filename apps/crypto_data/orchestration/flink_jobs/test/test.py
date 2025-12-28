from pyflink.table import EnvironmentSettings, TableEnvironment
from pyflink.table.expressions import col

# Streaming mode
env_settings = EnvironmentSettings.in_streaming_mode()
t_env = TableEnvironment.create(env_settings)

# Simple streaming source
data = [
    ("BTC", 65000.0),
    ("ETH", 3200.5),
    ("BTC", 65100.5),
    ("ETH", 3250.0),
]
table = t_env.from_elements(data, ["symbol", "price"])

# Compute average price per symbol
result = table.group_by(col("symbol")).select(
    col("symbol"), col("price").avg.alias("avg_price")
)

print("=== Average price per symbol (streaming mode) ===")
result.execute().print()
