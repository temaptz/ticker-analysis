import datetime
from pytz import timezone
from lib import docker, telegram

def error_logger(func):
    def wrapper(*args, **kwargs):
        function_name = func.__name__
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_error(method_name=function_name, error=e, debug_info=f'{args}:{kwargs}')
        return None
    return wrapper


def log_error(method_name: str, error: Exception = None, debug_info: str = None, is_telegram_send=docker.is_prod()) -> None:
    date_str = get_local_time_log_str()
    error_str = f'\033[91m[{date_str}] ERROR: {method_name}\033[0m'

    if error:
        error_str += f' Exception: {error}'

    if debug_info:
        error_str += f'; DEBUG INFO: {debug_info}'

    print(error_str)

    if is_telegram_send:
        telegram.send_message(error_str)


def log_info(message: str, output: any = None, is_send_telegram=False) -> None:
    date_str = get_local_time_log_str()
    out_str = f'\033[94m[{date_str}] {message}\033[0m'
    print(out_str, output)

    if is_send_telegram and docker.is_prod():
        telegram.send_message(message=out_str)


def get_local_time_log_str() -> str:
    return datetime.datetime.now(timezone('Europe/Moscow')).strftime('%Y-%m-%d_%H-%M-%S')