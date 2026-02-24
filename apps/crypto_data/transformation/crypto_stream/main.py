from shared_lib.flink import property_map

from .aggtrades import create_aggtrades_source
from .indicators import (
    create_indicator_view,
    create_indicators_sink,
    insert_indicators_clickhouse,
    insert_indicators_kafka,
)
from .klines import create_klines_sink, create_klines_view, insert_klines


def transform(t_env, props):
    # create sources and sinks
    kas_props = property_map(props, "kafka_aggtrades_source")
    kas_config = f"""(
        'connector' = 'kafka',
        'topic' = '{kas_props["topic"]}',
        'properties.bootstrap.servers' = '{kas_props["properties.bootstrap.servers"]}',
        'properties.group.id' = '{kas_props["properties.group.id"]}',
        'scan.startup.mode' = '{kas_props["scan.startup.mode"]}',
        'format' = 'json',
        'json.ignore-parse-errors' = 'true'
    )"""
    aggtrades_source = "aggtrades_source"
    create_aggtrades_source(t_env, table_name=aggtrades_source, config=kas_config)

    cks = property_map(props, "clickhouse_klines_sink")
    cks_config = f"""(
        'connector' = 'clickhouse',
        'url' = '{cks["url"]}',
        'database-name' = '{cks["database-name"]}',
        'table-name' = '{cks["table-name"]}',
        'username' = '{cks["username"]}',
        'password' = '{cks["password"]}',
        'sink.batch-size' = '5000',
        'sink.flush-interval' = '2s',
        'sink.max-retries' = '3',
        'sink.ignore-delete' = 'true'
    )"""
    klines_sink = "klines_sink"
    create_klines_sink(t_env, table_name=klines_sink, config=cks_config)

    cis_props = property_map(props, "clickhouse_indicators_sink")
    cis_config = f"""(
        'connector' = 'clickhouse',
        'url' = '{cis_props["url"]}',
        'database-name' = '{cis_props["database-name"]}',
        'table-name' = '{cis_props["table-name"]}',
        'username' = '{cis_props["username"]}',
        'password' = '{cis_props["password"]}',
        'sink.batch-size' = '5000',
        'sink.flush-interval' = '2s',
        'sink.max-retries' = '3',
        'sink.ignore-delete' = 'true'
    )"""
    clickhouse_indicators_sink = "clickhouse_indicators_sink"
    create_indicators_sink(
        t_env, table_name=clickhouse_indicators_sink, config=cis_config
    )

    kis_props = property_map(props, "kafka_indicators_sink")
    kis_config = f"""(
        'connector' = 'kafka',
        'topic' = '{kis_props["topic"]}',
        'properties.bootstrap.servers' = '{kis_props["properties.bootstrap.servers"]}',
        'format' = 'json',
        'key.format' = 'raw',
        'key.fields' = 'symbol',
        'json.timestamp-format.standard' = 'ISO-8601'
    )"""
    kafka_indicators_sink = "kafka_indicators_sink"
    create_indicators_sink(t_env, table_name=kafka_indicators_sink, config=kis_config)

    # create views
    klines_view = "klines_view"
    create_klines_view(t_env, view_name=klines_view, aggtrades_source=aggtrades_source)

    indicators_view = "indicators_view"
    create_indicator_view(t_env, view_name=indicators_view, klines_view=klines_view)

    # insert into sinks
    statement_set = t_env.create_statement_set()
    insert_klines(statement_set, klines_sink=klines_sink, klines_view=klines_view)
    insert_indicators_clickhouse(
        statement_set,
        indicators_sink=clickhouse_indicators_sink,
        indicators_view=indicators_view,
    )
    insert_indicators_kafka(
        statement_set,
        indicators_sink=kafka_indicators_sink,
        indicators_view=indicators_view,
    )
    return statement_set
