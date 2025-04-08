import datetime
from lib import docker, telegram

def error_logger(func):
    def wrapper(*args, **kwargs):
        function_name = func.__name__
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_error(method_name=function_name, error=e)
    return wrapper


def log_error(method_name: str, error: Exception = None) -> None:
    date_str = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    error_str = f'[{date_str}] ERROR: {method_name}'

    if error:
        error_str += f' -> {error}'

    print(error_str)

    if docker.is_prod():
        telegram.send_message(error_str)
