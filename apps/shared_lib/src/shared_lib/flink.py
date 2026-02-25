import json
import os

from pyflink.datastream import (
    StreamExecutionEnvironment,
)
from pyflink.table import EnvironmentSettings, StreamTableEnvironment


def get_application_properties(path):
    if os.path.isfile(path):
        with open(path, "r") as file:
            contents = file.read()
            properties = json.loads(contents)
            return properties
    else:
        raise FileNotFoundError(f'A file at "{path}" was not found')


def property_map(props, property_group_id) -> dict[str, str]:
    for prop in props:
        if prop["PropertyGroupId"] == property_group_id:
            return prop["PropertyMap"]
    raise ValueError(f"Property group {property_group_id} not found in properties")


def get_table_environment(parallelism: int = 1) -> StreamTableEnvironment:
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(parallelism)
    settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
    t_env = StreamTableEnvironment.create(env, environment_settings=settings)
    return t_env

def get_kafka_source_config(prop_map: dict[str, str]) -> str:
    return f"""(
        'connector' = 'kafka',
        'topic' = '{prop_map["topic"]}',
        'properties.bootstrap.servers' = '{prop_map["properties.bootstrap.servers"]}',
        'properties.group.id' = '{prop_map["properties.group.id"]}',
        'scan.startup.mode' = '{prop_map["scan.startup.mode"]}',
        'format' = 'json',
        'json.ignore-parse-errors' = 'true'
    )"""


def get_kinesis_source_config(prop_map: dict[str, str]) -> str:
    return f"""(
        'connector' = 'kinesis',
        'stream.arn' = '{prop_map["stream.arn"]}',
        'aws.region' = '{prop_map["aws.region"]}',
        'source.init.position' = '{prop_map["source.init.position"]}',
        'format' = 'json',
        'json.timestamp-format.standard' = 'ISO-8601'
    )"""


def get_clickhouse_sink_config(prop_map: dict[str, str]) -> str:
    return f"""(
        'connector' = 'clickhouse',
        'url' = '{prop_map["url"]}',
        'database-name' = '{prop_map["database-name"]}',
        'table-name' = '{prop_map["table-name"]}',
        'username' = '{prop_map["username"]}',
        'password' = '{prop_map["password"]}',
        'sink.batch-size' = '5000',
        'sink.flush-interval' = '2s',
        'sink.max-retries' = '3',
        'sink.ignore-delete' = 'true'
    )"""


def get_kafka_sink_config(prop_map: dict[str, str]) -> str:
    return f"""(
        'connector' = 'kafka',
        'topic' = '{prop_map["topic"]}',
        'properties.bootstrap.servers' = '{prop_map["properties.bootstrap.servers"]}',
        'format' = 'json',
        'key.format' = 'raw',
        'key.fields' = 'symbol',
        'json.timestamp-format.standard' = 'ISO-8601'
    )"""


def get_kinesis_sink_config(prop_map: dict[str, str]) -> str:
    return f"""(
        'connector' = 'kinesis',
        'stream.arn' = '{prop_map["stream.arn"]}',
        'aws.region' = '{prop_map["aws.region"]}',
        'sink.partitioner-field-delimiter' = ';',
        'sink.batch.max-size' = '100',
        'format' = 'json',
        'json.timestamp-format.standard' = 'ISO-8601'
    )"""