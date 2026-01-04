FROM apache/hive:4.0.0

# --- Postgres JDBC ---
ADD --chmod=644 https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.4/postgresql-42.7.4.jar \
    /opt/hive/lib/

# --- Hadoop S3A (CRITICAL: Hadoop classpath, not Hive) ---
ADD --chmod=644 https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar \
    /opt/hadoop/share/hadoop/common/lib/

ADD --chmod=644 https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar \
    /opt/hadoop/share/hadoop/common/lib/

# --- Iceberg Hive runtime (Hive side) ---
ADD --chmod=644 https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-hive-runtime/1.7.1/iceberg-hive-runtime-1.7.1.jar \
    /opt/hive/lib/

# # --- Configs ---
COPY hive-site.xml.template /opt/hive/conf/
COPY entrypoint.sh /entrypoint-wrapper.sh

USER root
RUN chmod +x /entrypoint-wrapper.sh

RUN apt-get update \
    && apt-get install -y gettext-base \
    && rm -rf /var/lib/apt/lists/*

USER hive
ENTRYPOINT ["/entrypoint-wrapper.sh"]