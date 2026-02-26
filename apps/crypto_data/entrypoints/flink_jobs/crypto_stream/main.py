import logging
import os

from shared_lib.flink import (
    get_application_properties,
    get_clickhouse_sink_config,
    get_kafka_sink_config,
    get_kafka_source_config,
    get_kinesis_sink_config,
    get_kinesis_source_config,
    get_table_environment,
    property_map,
)
from transformation.crypto_stream.main import run

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APPLICATION_PROPERTIES_FILE_PATH = "/etc/flink/application_properties.json"
ENV = os.getenv("ENV", "")

if __name__ == "__main__":
    t_env = get_table_environment(parallelism=1)

    if ENV == "local":
        CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
        APPLICATION_PROPERTIES_FILE_PATH = os.path.join(
            CURRENT_DIR, "application_properties.json"
        )
        t_env.get_config().get_configuration().set_string(
            "pipeline.jars",
            "file:///" + CURRENT_DIR + "/target/pyflink-dependencies.jar",
        )

    props = get_application_properties(APPLICATION_PROPERTIES_FILE_PATH)
    configs: dict[str, str] = {}

    aggtrades_source_props = property_map(props, "stream_aggtrades_source")
    aggtrades_source_table = "aggtrades_source_table"
    configs[aggtrades_source_table] = (
        get_kafka_source_config(aggtrades_source_props)
        if ENV == "local"
        else get_kinesis_source_config(aggtrades_source_props)
    )

    klines_sink_props = property_map(props, "clickhouse_klines_sink")
    klines_sink_table = "klines_sink_table"
    configs[klines_sink_table] = get_clickhouse_sink_config(klines_sink_props)

    clickhouse_indicators_sink_props = property_map(props, "clickhouse_indicators_sink")
    clickhouse_indicators_sink_table = "clickhouse_indicators_sink_table"
    configs[clickhouse_indicators_sink_table] = get_clickhouse_sink_config(
        clickhouse_indicators_sink_props
    )

    stream_indicators_sink_props = property_map(props, "stream_indicators_sink")
    stream_indicators_sink_table = "stream_indicators_sink_table"
    configs[stream_indicators_sink_table] = (
        get_kafka_sink_config(stream_indicators_sink_props)
        if ENV == "local"
        else get_kinesis_sink_config(stream_indicators_sink_props)
    )

    statement_set = run(
        t_env,
        configs=configs,
        aggtrades_source_table=aggtrades_source_table,
        klines_sink_table=klines_sink_table,
        clickhouse_indicators_sink_table=clickhouse_indicators_sink_table,
        stream_indicators_sink_table=stream_indicators_sink_table,
    )

    if ENV == "local":
        statement_set.execute().wait()  # block only locally
    else:
        statement_set.execute()  # non-blocking in KDA
