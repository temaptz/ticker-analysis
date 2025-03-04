import datetime
from lib.learn.ta_1.learning_card import LearningCard
from lib.learn.ta_1 import learn
from lib import date_utils
from lib.db import predictions_ta_1_db
from tinkoff.invest import CandleInterval


def get_prediction_ta_1_by_uid(uid: str) -> float or None:
    c = LearningCard()
    c.load_by_uid(uid=uid)
    x = c.get_x()

    try:
        return learn.predict(x)
    except Exception as e:
        print('ERROR get_prediction_ta_1_by_uid', e)
        return None


# @TODO interval
def get_prediction_ta_1_graph_by_uid(uid: str, date_from: datetime.datetime, date_to: datetime.datetime, interval: CandleInterval) -> list:
    timedelta = datetime.timedelta(days=30)

    try:
        result = list()

        for i in predictions_ta_1_db.get_predictions_by_uid_date(
            uid=uid,
            date_from=date_from - timedelta,
            date_to=date_to - timedelta,
        ):
            result.append({
                'prediction': i[1],
                'date': (date_utils.parse_date(i[2]) + timedelta).isoformat(),
            })

        return result
    except Exception as e:
        print('ERROR get_prediction_ta_1_graph_by_uid', e)
        return []
