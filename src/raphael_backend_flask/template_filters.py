import datetime


def format_offset(seconds: float) -> str:
    seconds = int(seconds)
    return str(datetime.timedelta(seconds=seconds))
