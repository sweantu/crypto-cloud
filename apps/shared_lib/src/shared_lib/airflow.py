import os

from airflow.exceptions import AirflowFailException


def require_env(keys: list[str]) -> None:
    for key in keys:
        if not os.getenv(key):
            raise AirflowFailException(f"Missing env var: {key}")
