import datetime

from numpy.lib.utils import source
from collections import defaultdict

from lib.learn.ta_1.learning_card import LearningCard
from lib.learn.ta_1 import learn
from lib.learn import ta_1_1, ta_1_2, ta_2, const
from lib import date_utils, logger, utils
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


def get_prediction_ta_1_1_by_uid(uid: str) -> float or None:
    c = ta_1_1.LearningCard()
    c.load_by_uid(uid=uid, fill_empty=True)
    x = c.get_x()

    try:
        return ta_1_1.predict(x)
    except Exception as e:
        print('ERROR get_prediction_ta_1_1_by_uid', e)
        return None


def get_prediction_ta_1_graph(uid: str, date_from: datetime.datetime, date_to: datetime.datetime, interval: CandleInterval) -> list:
    timedelta = datetime.timedelta(days=30)

    try:
        result = list()

        for i in predictions_db.get_predictions_by_uid_date(
            uid=uid,
            date_from=date_from - timedelta,
            date_to=date_to - timedelta,
            model_name=const.TA_1,
        ):
            result.append({
                'prediction': i.prediction,
                'date': (date_utils.parse_date(i.date) + timedelta).isoformat(),
            })

        return utils.filter_array_by_date_interval(source=result, date_field='date', interval=interval)
    except Exception as e:
        print('ERROR get_prediction_ta_1_graph_by_uid', e)
        return []


def get_prediction_ta_1_1_graph(uid: str, date_from: datetime.datetime, date_to: datetime.datetime, interval: CandleInterval) -> list:
    timedelta = datetime.timedelta(days=30)

    try:
        result = list()

        for i in predictions_db.get_predictions_by_uid_date(
                uid=uid,
                date_from=date_from - timedelta,
                date_to=date_to - timedelta,
                model_name=const.TA_1_1,
        ):
            result.append({
                'prediction': i.prediction,
                'date': (date_utils.parse_date(i.date) + timedelta).isoformat(),
            })

        return utils.filter_array_by_date_interval(source=result, date_field='date', interval=interval)
    except Exception as e:
        print('ERROR get_prediction_ta_1_1_graph_by_uid', e)
        return []


def get_prediction_ta_1_2_graph(uid: str, date_from: datetime.datetime, date_to: datetime.datetime, interval: CandleInterval) -> list:
    try:
        result = list()

        for date in date_utils.get_dates_interval_list(
                date_from=date_from,
                date_to=date_to,
                interval_seconds=date_utils.get_interval_sec_by_candle(interval)
        ):
            prediction = ta_1_2.predict_future(
                instrument_uid=uid,
                date_target=date,
            )

            if prediction is not None:
                result.append({
                    'prediction': prediction,
                    'date': date,
                })

        return result
    except Exception as e:
        print('ERROR get_prediction_ta_1_2_graph_by_uid', e)
        return []


def get_prediction_ta_2_graph(uid: str, date_from: datetime.datetime, date_to: datetime.datetime, interval: CandleInterval) -> list:
    try:
        result = list()

        for date in date_utils.get_dates_interval_list(
                date_from=date_from,
                date_to=date_to,
                interval_seconds=date_utils.get_interval_sec_by_candle(interval)
        ):
            prediction = ta_2.predict_future(
                instrument_uid=uid,
                date_target=date,
            )

            if prediction is not None:
                result.append({
                    'prediction': prediction,
                    'date': date,
                })

        return result
    except Exception as e:
        print('ERROR get_prediction_ta_2_graph_by_uid', e)
        return []


@logger.error_logger
def get_prediction_ta_2_history_graph(
        uid: str,
        date_from: datetime.datetime,
        date_to: datetime.datetime,
        interval: CandleInterval,
) -> dict:
    result = dict()

    for prediction in predictions_db.get_predictions_by_uid_date(
        uid=uid,
        date_from=date_from,
        date_to=date_to,
        model_name=const.TA_2,
    ):
        key = prediction.date

        if not result[key]:
            result[key] = []

        result[key].append({
            'prediction': prediction.prediction,
            'date': date_utils.parse_date(prediction.date),
        })

    return result


@logger.error_logger
def get_predictions_consensus(instrument_uid: str, date_target: datetime.datetime) -> float or None:
    pred_ta_1 = get_prediction_ta_1_by_uid(uid=instrument_uid)
    pred_ta_1_1 = get_prediction_ta_1_1_by_uid(uid=instrument_uid)
    pred_ta_1_2 = ta_1_2.predict_future(instrument_uid=instrument_uid, date_target=date_target)
    pred_list = []

    if pred_ta_1 is not None:
        pred_list.append(pred_ta_1)

    if pred_ta_1_1 is not None:
        pred_list.append(pred_ta_1_1)

    if pred_ta_1_2 is not None:
        pred_list.append(pred_ta_1_2)

    if len(pred_list) > 0:
        return sum(pred_list) / len(pred_list)

    return None
