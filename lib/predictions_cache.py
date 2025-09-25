import datetime
from lib import learn, redis_utils


def get_prediction_cache(
        instrument_uid: str,
        model_name: learn.model,
        date_target: datetime.datetime,
    ) -> float or None:
    if cache_key := get_cache_key(
            instrument_uid=instrument_uid,
            model_name=model_name,
            date_target=date_target,
    ):
        if cached := redis_utils.storage_get(key=cache_key):
            return float(cached)
    return None


def set_prediction_cache(
        instrument_uid: str,
        model_name: learn.model,
        date_target: datetime.datetime,
        prediction: float,
):
    if cache_key := get_cache_key(
            instrument_uid=instrument_uid,
            model_name=model_name,
            date_target=date_target,
    ):
        redis_utils.storage_set(
            key=cache_key,
            value=prediction,
            ttl_sec=(3600 * 24 * 30 * 3),
        )


def get_cache_key(
        instrument_uid: str,
        model_name: learn.model,
        date_target: datetime.datetime,
) -> str:
    return f'instrument_uid:{instrument_uid};model_name:{model_name};date_target:{date_target}'
