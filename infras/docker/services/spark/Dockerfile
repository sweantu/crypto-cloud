FROM apache/spark:3.5.4-java17

USER root

RUN apt-get update && \
    apt-get install -y python3.11 python3.11-distutils python3.11-venv python3-pip && \
    ln -sf /usr/bin/python3.11 /usr/bin/python && \
    ln -sf /usr/bin/python3.11 /usr/bin/python3 && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir pyspark==3.5.4

USER spark

ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

WORKDIR /opt/spark/work-dir