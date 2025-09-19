import datetime
from types import SimpleNamespace
import tinkoff.invest
import json
import pickle
from lib import logger


def to_json(obj, ensure_ascii=True, is_pretty=False) -> str or None:
    try:
        return json.dumps(
            get_dict_by_object_recursive(obj),
            ensure_ascii=ensure_ascii,
            indent=(4 if is_pretty else None),
        )
    except Exception as e:
        print('ERROR to_json', e)
        return None


def from_json(json_str: str) -> dict or None:
    try:
        return get_dict_by_object_recursive(json.loads(json_str))
    except Exception as e:
        print('ERROR from_json', e)
    return None


def get_dict_by_object_recursive(data):
    if isinstance(data, dict):  # Если это словарь
        return {key: get_dict_by_object_recursive(value) for key, value in data.items()}
    elif isinstance(data, list):  # Если это список
        return [get_dict_by_object_recursive(item) for item in data]
    elif isinstance(data, tuple):  # Если это кортеж
        return [get_dict_by_object_recursive(item) for item in data]
    elif isinstance(data, set):  # Если это множество
        return [get_dict_by_object_recursive(item) for item in data]  # Преобразуем в список
    elif hasattr(data, "__dict__"):  # Если это объект с атрибутами
        return get_dict_by_object_recursive(data.__dict__)
    elif isinstance(data, (int, float, bool, str, type(None))):  # Примитивные типы
        return data
    else:
        return str(data)  # Если неизвестный тип, конвертируем в строку


def get_dict_by_object(input) -> dict:
    result: dict = {}

    for property_name in dir(input):
        if property_name[0:2] != '__':
            property_value = getattr(input, property_name)
            is_quotation = isinstance(property_value, tinkoff.invest.Quotation)
            is_datetime = isinstance(property_value, datetime.datetime)

            if is_quotation:
                property_value = get_dict_by_object_recursive(property_value)

            if is_datetime:
                property_value = datetime.datetime.isoformat(property_value)

            if type(property_value) in (str, int, float, bool, dict, list):
                result.update({property_name: property_value})

    return result


def db_serialize(data: any) -> bytes:
    """
    Стабильная сериализация объекта в байты для хранения в Redis.
    Использует pickle (Python built-in).
    """
    try:
        return pickle.dumps(data)
    except Exception as e:
        print(f'Ошибка сериализации объекта db_serialize: {e}')

    return data


def db_deserialize(data: bytes or str)-> any:
    """
    Стабильная десериализация байтов из Redis обратно в объект Python.
    """
    try:
        if isinstance(data, str):
            # Иногда postgres автоматически декодирует BYTEA в str (например, в ORM)
            data = data.encode('utf-8')
        return pickle.loads(data)
    except Exception as e:
        print(f'Ошибка десериализации объекта db_deserialize: {e}')

    return data


def dict_to_object_recursive(d):
    if isinstance(d, dict):
        obj_dict = {}
        for k, v in d.items():
            if not isinstance(k, str) or not k.isidentifier():
                continue
            try:
                obj_dict[k] = dict_to_object_recursive(v)
            except Exception as e:
                logger.log_error(method_name='dict_to_object_recursive_1', error=e, is_telegram_send=False)
        return SimpleNamespace(**obj_dict)
    elif isinstance(d, list):
        return [dict_to_object_recursive(i) for i in d]
    else:
        return d
