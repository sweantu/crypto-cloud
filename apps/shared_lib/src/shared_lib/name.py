import os

from shared_lib.local import LOCAL_ENV

PROJECT_PREFIX = os.getenv("PROJECT_PREFIX", "")


def get_stream_name(name: str) -> str:
    return name if LOCAL_ENV else f"{PROJECT_PREFIX}-{name}"


def get_glue_job_name(name: str) -> str:
    return name if LOCAL_ENV else f"{PROJECT_PREFIX}-{name}"
