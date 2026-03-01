import os

LOCAL_RUN = os.getenv("LOCAL_RUN", "false").lower() == "true"
LOCAL_ENV = os.getenv("ENV", "").lower() == "local"
