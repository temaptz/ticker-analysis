import datetime
from pytz import timezone
from lib import docker, telegram

def error_logger(func):
    def wrapper(*args, **kwargs):
        function_name = func.__name__
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_error(method_name=function_name, error=e)
    return wrapper


def log_error(method_name: str, error: Exception = None, debug_info: str = None) -> None:
    date_str = get_local_time_log_str()
    error_str = f'[{date_str}] ERROR: {method_name}; DEBUG INFO: {debug_info}'

    if error:
        error_str += f' -> {error}'

    print(error_str)

    if docker.is_prod():
        telegram.send_message(error_str)


def log_info(message: str, output: any = None) -> None:
    date_str = get_local_time_log_str()
    print(f'\033[94m[{date_str}] {message}\033[0m', output)


def get_local_time_log_str() -> str:
    return datetime.datetime.now(timezone('Europe/Moscow')).strftime('%Y-%m-%d_%H-%M-%S')