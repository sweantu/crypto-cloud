from shared_lib.flink import (
    get_clickhouse_sink_config,
    get_kafka_sink_config,
    get_kafka_source_config,
    property_map,
)

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
    kas_groupid = "kafka_aggtrades_source"
    kas_props = property_map(props, kas_groupid)
    kas_config = get_kafka_source_config(kas_props)
    create_aggtrades_source(t_env, table_name=kas_groupid, config=kas_config)

    cks_groupid = "clickhouse_klines_sink"
    cks_props = property_map(props, cks_groupid)
    cks_config = get_clickhouse_sink_config(cks_props)
    create_klines_sink(t_env, table_name=cks_groupid, config=cks_config)

    cis_groupid = "clickhouse_indicators_sink"
    cis_props = property_map(props, cis_groupid)
    cis_config = get_clickhouse_sink_config(cis_props)
    create_indicators_sink(t_env, table_name=cis_groupid, config=cis_config)

    kis_groupid = "kafka_indicators_sink"
    kis_props = property_map(props, kis_groupid)
    kis_config = get_kafka_sink_config(kis_props)
    create_indicators_sink(t_env, table_name=kis_groupid, config=kis_config)

    # create views
    klines_view = "klines_view"
    create_klines_view(t_env, view_name=klines_view, aggtrades_source=kas_groupid)

    indicators_view = "indicators_view"
    create_indicator_view(t_env, view_name=indicators_view, klines_view=klines_view)

    # insert into sinks
    statement_set = t_env.create_statement_set()
    insert_klines(statement_set, klines_sink=cks_groupid, klines_view=klines_view)
    insert_indicators_clickhouse(
        statement_set,
        indicators_sink=cis_groupid,
        indicators_view=indicators_view,
    )
    insert_indicators_kafka(
        statement_set,
        indicators_sink=kis_groupid,
        indicators_view=indicators_view,
    )
    return statement_set
