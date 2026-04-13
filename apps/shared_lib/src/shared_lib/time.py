import datetime


def get_current_timestamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%SZ")
