import logging
import os

from shared_lib.flink import (
    get_application_properties,
    get_table_environment,
)
from transformation.crypto_stream.main import transform

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APPLICATION_PROPERTIES_FILE_PATH = "/etc/flink/application_properties.json"

if __name__ == "__main__":
    t_env = get_table_environment(parallelism=1)
    is_local = True if os.environ.get("FLINK_LOCAL") else False
    if is_local:
        CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
        APPLICATION_PROPERTIES_FILE_PATH = os.path.join(
            CURRENT_DIR, "application_properties.json"
        )
        t_env.get_config().get_configuration().set_string(
            "pipeline.jars",
            "file:///" + CURRENT_DIR + "/target/pyflink-dependencies.jar",
        )

    props = get_application_properties(APPLICATION_PROPERTIES_FILE_PATH)

    statement_set = transform(t_env, props)
    if is_local:
        statement_set.execute().wait()  # block only locally
    else:
        statement_set.execute()  # non-blocking in KDA
