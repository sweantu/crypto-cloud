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
