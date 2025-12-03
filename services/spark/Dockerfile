FROM apache/spark:3.5.4-java17

USER root

RUN apt-get update && \
    apt-get install -y python3.11 python3.11-distutils python3.11-venv python3-pip && \
    ln -sf /usr/bin/python3.11 /usr/bin/python && \
    ln -sf /usr/bin/python3.11 /usr/bin/python3 && \
    rm -rf /var/lib/apt/lists/*

# --- Iceberg 1.7.1 for Spark 3.5 ---
ADD https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.7.1/iceberg-spark-runtime-3.5_2.12-1.7.1.jar \
    /opt/spark/jars/iceberg-spark-runtime-3.5_2.12-1.7.1.jar

# --- S3A / MinIO support ---
ADD https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.6/hadoop-aws-3.3.6.jar \
    /opt/spark/jars/hadoop-aws-3.3.6.jar

ADD https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.632/aws-java-sdk-bundle-1.12.632.jar \
    /opt/spark/jars/aws-java-sdk-bundle-1.12.632.jar

RUN pip3 install --no-cache-dir pyspark==3.5.4

USER spark

ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

WORKDIR /opt/spark/work-dir