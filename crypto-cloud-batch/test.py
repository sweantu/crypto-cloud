from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col

# Create Spark session (local mode)
spark = (
    SparkSession.builder.appName("LocalSparkTest")
    .master("local[*]")
    .config("spark.ui.showConsoleProgress", "true")
    .getOrCreate()
)

print(f"✅ Spark version: {spark.version}")

# Create a simple DataFrame
data = [
    ("Alice", 34, "NY"),
    ("Bob", 45, "CA"),
    ("Charlie", 29, "NY"),
    ("Diana", 40, "TX"),
]
columns = ["name", "age", "state"]

df = spark.createDataFrame(data, columns)

# Basic operations
print("=== Original Data ===")
df.show()

# Filter and aggregation
df_filtered = df.filter(col("age") > 30)
print("=== Filtered (age > 30) ===")
df_filtered.show()

df_grouped = df.groupBy("state").agg(avg("age").alias("avg_age"))
print("=== Average age by state ===")
df_grouped.show()

# Stop session
spark.stop()
