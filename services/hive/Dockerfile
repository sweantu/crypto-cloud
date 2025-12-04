FROM apache/hive:4.0.1

USER root

# Postgres JDBC
ADD --chmod=644 \
    https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.4/postgresql-42.7.4.jar \
    /opt/hive/lib/postgres.jar

# S3 / MinIO support (Hadoop already bundled, this ensures S3A works)
# Usually not needed, but safe:
ADD --chmod=644 \
    https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.632/aws-java-sdk-bundle-1.12.632.jar \
    /opt/hive/lib/aws-java-sdk-bundle.jar

# Your config
COPY services/hive/hive-site.xml /opt/hive/conf/hive-site.xml

USER hive