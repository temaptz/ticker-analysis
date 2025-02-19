from lib.learn.ta_1.learning_card import LearningCard
from lib.learn.ta_1 import learn
from lib.db import predictions_ta_1_db


def get_prediction_ta_1_by_uid(uid: str) -> float or None:
    c = LearningCard()
    c.load_by_uid(uid=uid)
    x = c.get_x()

    try:
        return learn.predict(x)
    except Exception as e:
        print('ERROR get_prediction_ta_1_by_uid', e)
        return None


def get_prediction_ta_1_graph_by_uid(uid: str) -> list:
    try:
        result = list()

        for i in predictions_ta_1_db.get_predictions_by_uid(uid):
            result.append({
                'prediction': i[1],
                'date': i[2],
            })
            print(i)

        print(result)

        return result
    except Exception as e:
        print('ERROR get_prediction_ta_1_graph_by_uid', e)
        return []
