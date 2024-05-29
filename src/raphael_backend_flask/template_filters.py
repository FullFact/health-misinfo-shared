import datetime


def format_offset(seconds: float) -> str:
    """
    Given an offset time in seconds, returns a nicely
    formatted string.
    """
    seconds = int(seconds)
    formatted = str(datetime.timedelta(seconds=seconds))
    if formatted.startswith("0:"):
        # if hours is zero, remove it
        formatted = formatted[2:]
    return formatted
