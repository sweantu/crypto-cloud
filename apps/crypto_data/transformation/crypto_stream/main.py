from .aggtrades import create_aggtrades_source
from .indicators import (
    create_indicator_view,
    create_indicators_sink,
    insert_indicators_clickhouse,
    insert_indicators_stream,
)
from .klines import create_klines_sink, create_klines_view, insert_klines


def run(
    t_env,
    configs,
    aggtrades_source_table,
    klines_sink_table,
    clickhouse_indicators_sink_table,
    stream_indicators_sink_table,
):
    # create sources and sinks
    create_aggtrades_source(
        t_env, table_name=aggtrades_source_table, config=configs[aggtrades_source_table]
    )
    create_klines_sink(
        t_env, table_name=klines_sink_table, config=configs[klines_sink_table]
    )
    create_indicators_sink(
        t_env,
        table_name=clickhouse_indicators_sink_table,
        config=configs[clickhouse_indicators_sink_table],
    )
    create_indicators_sink(
        t_env,
        table_name=stream_indicators_sink_table,
        config=configs[stream_indicators_sink_table],
    )

    # create views
    klines_view = "klines_view"
    create_klines_view(
        t_env, view_name=klines_view, aggtrades_source_table=aggtrades_source_table
    )
    indicators_view = "indicators_view"
    create_indicator_view(t_env, view_name=indicators_view, klines_view=klines_view)

    # insert into sinks
    statement_set = t_env.create_statement_set()
    insert_klines(
        statement_set, klines_sink_table=klines_sink_table, klines_view=klines_view
    )
    insert_indicators_clickhouse(
        statement_set,
        indicators_sink_table=clickhouse_indicators_sink_table,
        indicators_view=indicators_view,
    )
    insert_indicators_stream(
        statement_set,
        indicators_sink_table=stream_indicators_sink_table,
        indicators_view=indicators_view,
    )
    return statement_set
