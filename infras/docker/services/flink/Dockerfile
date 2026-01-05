FROM apache/flink:1.20.3

USER root

RUN apt-get update && \
    apt-get install -y \
    python3.11 \
    python3.11-distutils \
    python3.11-venv \
    python3-pip \
    python3.11-dev \
    openjdk-11-jdk \
    build-essential \
    && ln -sf /usr/bin/python3.11 /usr/bin/python \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && ln -s /usr/lib/jvm/java-11-openjdk-*/include /opt/java/openjdk/include \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/opt/java/openjdk
ENV PATH=$JAVA_HOME/bin:$PATH

RUN pip3 install --no-cache-dir apache-flink==1.20.3

USER flink