import datetime
import tinkoff.invest


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
