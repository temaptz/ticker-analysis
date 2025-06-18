import datetime
from lib.learn.ta_1.learning_card import LearningCard
from lib.learn.ta_1 import learn
from lib.learn import ta_1_1, ta_1_2, ta_2, ta_2_1, model
from lib import date_utils, logger, utils, instruments, cache
from lib.db_2 import predictions_db
from tinkoff.invest import CandleInterval


def get_prediction_ta_1_by_uid(uid: str) -> float or None:
    c = LearningCard()
    c.load_by_uid(uid=uid, fill_empty=True)
    x = c.get_x()

    try:
        return learn.predict(x)
    except Exception as e:
        print('ERROR get_prediction_ta_1_by_uid', e)
        return None


def get_relative_prediction_ta_1_by_uid(uid: str) -> float or None:
    c = LearningCard()
    c.load_by_uid(uid=uid, fill_empty=True)
    x = c.get_x()

    try:
        if c.price:
            if prediction := learn.predict(x):
                return utils.get_change_relative_by_price(
                    main_price=c.price,
                    next_price=prediction,
                )
    except Exception as e:
        print('ERROR get_relative_prediction_ta_1_by_uid', e)

    return None


def get_prediction_ta_1_1_by_uid(uid: str) -> float or None:
    c = ta_1_1.LearningCard()
    c.load_by_uid(uid=uid, fill_empty=True)
    x = c.get_x()

    try:
        return ta_1_1.predict(x)
    except Exception as e:
        print('ERROR get_prediction_ta_1_1_by_uid', e)
        return None


def get_relative_prediction_ta_1_1_by_uid(uid: str) -> float or None:
    c = ta_1_1.LearningCard()
    c.load_by_uid(uid=uid, fill_empty=True)
    x = c.get_x()

    try:
        if c.price:
            if prediction := ta_1_1.predict(x):
                return utils.get_change_relative_by_price(
                    main_price=c.price,
                    next_price=prediction,
                )
    except Exception as e:
        print('ERROR get_prediction_ta_1_1_by_uid', e)

    return None


def get_prediction_ta_1_graph(uid: str, date_from: datetime.datetime, date_to: datetime.datetime, interval: CandleInterval) -> list:
    try:
        result = list()

        for i in predictions_db.get_predictions_by_uid_date(
            uid=uid,
            date_from=date_from,
            date_to=date_to,
            model_name=model.TA_1,
        ):
            result.append({
                'prediction': i.prediction,
                'date': date_utils.parse_date(i.target_date).isoformat(),
            })

        return utils.filter_array_by_date_interval(source=result, date_field='date', interval=interval)
    except Exception as e:
        print('ERROR get_prediction_ta_1_graph_by_uid', e)
        return []


def get_prediction_ta_1_1_graph(uid: str, date_from: datetime.datetime, date_to: datetime.datetime, interval: CandleInterval) -> list:
    try:
        result = list()

        for i in predictions_db.get_predictions_by_uid_date(
                uid=uid,
                date_from=date_from,
                date_to=date_to,
                model_name=model.TA_1_1,
        ):
            result.append({
                'prediction': i.prediction,
                'date': date_utils.parse_date(i.target_date).isoformat(),
            })

        return utils.filter_array_by_date_interval(source=result, date_field='date', interval=interval)
    except Exception as e:
        print('ERROR get_prediction_ta_1_1_graph_by_uid', e)
        return []


def get_prediction_graph(uid: str, model_name: str, date_from: datetime.datetime, date_to: datetime.datetime, interval: CandleInterval) -> list:
    try:
        result = list()
        date_from_utc = date_utils.convert_to_utc(
            datetime.datetime.combine(
                date_from,
                datetime.time(hour=12, minute=0, second=0, microsecond=0)
            )
        )
        date_to_utc = date_utils.convert_to_utc(date_to)

        for date in date_utils.get_dates_interval_list(
                date_from=date_from_utc,
                date_to=date_to_utc,
                interval_seconds=date_utils.get_interval_sec_by_candle(interval)
        ):
            prediction_item = None

            if model_name == model.TA_1_2:
                prediction_item = ta_1_2.predict_future(
                    instrument_uid=uid,
                    date_target=date,
                )
            elif model_name == model.TA_2:
                prediction_item = ta_2.predict_future(
                    instrument_uid=uid,
                    date_target=date,
                )
            elif model_name == model.TA_2_1:
                prediction_item = ta_2_1.predict_future(
                    instrument_uid=uid,
                    date_target=date,
                )

            if prediction_item is not None:
                result.append({
                    'prediction': prediction_item,
                    'date': date,
                })

        return result
    except Exception as e:
        print('ERROR get_prediction_graph_by_uid', e)

    return []


@logger.error_logger
def get_prediction_history_graph(
        uid: str,
        model_name: str,
        date_from: datetime.datetime,
        date_to: datetime.datetime,
        interval: CandleInterval,
) -> dict:
    result = {}

    for prediction in predictions_db.get_predictions_by_uid_date(
        uid=uid,
        date_from=date_from,
        date_to=date_to,
        model_name=model_name,
    ):
        key = date_utils.parse_date(prediction.date).isoformat()
        target_dt = date_utils.parse_date(prediction.target_date)

        if key not in result:
            result[key] = []

        if not any(p['date'] == target_dt for p in result[key]):
            result[key].append({
                'prediction': prediction.prediction,
                'date': target_dt,
            })

    return result


@cache.ttl_cache(ttl=3600, is_skip_empty=True)
@logger.error_logger
def get_predictions_consensus(instrument_uid: str, date_target: datetime.datetime) -> float or None:
    pred_ta_1 = get_prediction_ta_1_by_uid(uid=instrument_uid)
    pred_ta_1_1 = get_prediction_ta_1_1_by_uid(uid=instrument_uid)
    pred_ta_1_2 = ta_1_2.predict_future(instrument_uid=instrument_uid, date_target=date_target)
    pred_ta_2 = ta_2.predict_future(instrument_uid=instrument_uid, date_target=date_target)
    pred_ta_2_1 = ta_2_1.predict_future(instrument_uid=instrument_uid, date_target=date_target)

    if pred_ta_2_1 or pred_ta_2 or pred_ta_1_2:
        weights = {
            'pred_ta_1': 1,
            'pred_ta_1_1': 1,
            'pred_ta_1_2': 5,
            'pred_ta_2': 3,
            'pred_ta_2_1': 7,
        }

        # Собираем значения и веса
        pred_values = [
            (pred_ta_1, weights['pred_ta_1']),
            (pred_ta_1_1, weights['pred_ta_1_1']),
            (pred_ta_1_2, weights['pred_ta_1_2']),
            (pred_ta_2, weights['pred_ta_2']),
            (pred_ta_2_1, weights['pred_ta_2_1']),
        ]

        # Считаем взвешенное среднее только по существующим значениям
        weighted_sum = 0
        total_weight = 0
        for value, weight in pred_values:
            if value is not None:
                weighted_sum += value * weight
                total_weight += weight

        if total_weight > 0:
            return weighted_sum / total_weight

    return None


def get_relative_predictions_consensus(instrument_uid: str, date_target: datetime.datetime) -> float or None:
    if current_price := instruments.get_instrument_last_price_by_uid(uid=instrument_uid):
        if consensus := get_predictions_consensus(instrument_uid=instrument_uid, date_target=date_target):
            return utils.get_change_relative_by_price(
                main_price=current_price,
                next_price=consensus,
            )

    return None
