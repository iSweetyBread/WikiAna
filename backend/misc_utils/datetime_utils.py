import datetime

# quasi library to work with Wikimedia API times
# mainly for converting between datetime objects and different datetime strings

def get_current_utc_time():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def convert_continue_to_utc_iso(string: str) -> str:
    return datetime.datetime.strptime(string, '%Y%m%d%H%M%S').isoformat() + 'Z'

def get_current_midnight():
    return datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

def convert_to_utc_iso(time: datetime.datetime) -> str:
    return time.strftime('%Y-%m-%dT%H:%M:%SZ')

def convert_to_datetime(string: str) -> datetime.datetime:
    return datetime.datetime.strptime(string, '%Y-%m-%dT%H:%M:%SZ')