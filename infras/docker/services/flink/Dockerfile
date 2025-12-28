FROM apache/flink:1.20.3-java11

USER root

# -------------------------------
# 1. Install Python 3.11
# -------------------------------
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.11 python3.11-distutils python3-pip && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    ln -s /usr/bin/python3.11 /usr/bin/python3 && \
    python --version && \
    rm -rf /var/lib/apt/lists/*

# -------------------------------
# 2. Install PyFlink
# -------------------------------
RUN pip install --no-cache-dir apache-flink==1.20.3

# -------------------------------
# 3. Flink Libraries Directory
# -------------------------------
ENV FLINK_LIB_DIR=/opt/flink/lib
WORKDIR $FLINK_LIB_DIR

# -------------------------------
# 4. Kafka SQL Connector (1.20)
# -------------------------------
RUN wget -q https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.3.0-1.20/flink-sql-connector-kafka-3.3.0-1.20.jar

# -------------------------------
# 5. JDBC Connector
# -------------------------------
RUN wget -q https://repo1.maven.org/maven2/org/apache/flink/flink-connector-jdbc/3.3.0-1.20/flink-connector-jdbc-3.3.0-1.20.jar

# -------------------------------
# 6. PostgreSQL Driver
# -------------------------------
RUN wget -q https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.3/postgresql-42.7.3.jar

# -------------------------------
# 7. ClickHouse SQL Connector
# -------------------------------
RUN wget -q https://repo1.maven.org/maven2/name/nkonev/flink/flink-sql-connector-clickhouse/1.17.1-8/flink-sql-connector-clickhouse-1.17.1-8.jar

# -------------------------------
# 8. Apache Iceberg 1.7.1 (Flink 1.20)
# -------------------------------
RUN wget -q https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-flink-runtime-1.20/1.7.1/iceberg-flink-runtime-1.20-1.7.1.jar

# -------------------------------
# 9. Hadoop + AWS (MinIO / S3)
# -------------------------------
RUN wget -q https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-client/3.3.6/hadoop-client-3.3.6.jar && \
    wget -q https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/2.25.40/bundle-2.25.40.jar && \
    wget -q https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-aws/1.7.1/iceberg-aws-1.7.1.jar

# -------------------------------
# 10. PyFlink Environment Variables
# -------------------------------
ENV FLINK_PYTHON_EXECUTABLE=/usr/bin/python3.11
ENV PYTHONPATH=/opt/flink/opt/python:/opt/flink/lib

# -------------------------------
# 11. Cleanup & Security
# -------------------------------
RUN rm -rf /tmp/*

USER flink