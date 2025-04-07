import datetime
import tinkoff.invest
import json
import pickle


def to_json(obj) -> str or None:
    try:
        return json.dumps(get_dict_by_object_recursive(obj))
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
                property_value = get_dict_by_object(property_value)

            if is_datetime:
                property_value = datetime.datetime.isoformat(property_value)

            if type(property_value) in (str, int, float, bool, dict, list):
                result.update({property_name: property_value})

    return result


def serialize_for_cache(data: any) -> bytes:
    """
    Стабильная сериализация объекта в байты для хранения в Redis.
    Использует pickle (Python built-in).
    """
    try:
        return pickle.dumps(data)
    except Exception as e:
        raise ValueError(f'Ошибка сериализации объекта serialize_for_cache: {e}')


def deserialize_from_cache(data: bytes):
    """
    Стабильная десериализация байтов из Redis обратно в объект Python.
    """
    try:
        return pickle.loads(data)
    except Exception as e:
        raise ValueError(f'Ошибка десериализации объекта deserialize_from_cache: {e}')
