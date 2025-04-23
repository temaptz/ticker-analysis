import time
import threading
from functools import wraps
from lib import logger

_last_call_time = 0
_lock = threading.Lock()

def throttle_once_per_second(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        global _last_call_time
        with _lock:
            now = time.time()
            wait_time = max(0, 1 - (now - _last_call_time))
            if wait_time > 0:
                logger.log_info(message=f'WILL THROTTLE TIME: {time} BEFORE CALL METHOD: {func.__name__}')
                time.sleep(wait_time)
            _last_call_time = time.time()
        return func(*args, **kwargs)
    return wrapper
