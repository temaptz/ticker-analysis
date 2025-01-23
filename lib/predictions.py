from lib.learning_card import LearningCard
from lib import learn
from lib.db import predictions_db


def get_prediction_by_uid(uid: str) -> float:
    c = LearningCard()
    c.load_by_uid(uid=uid)
    x = c.get_x()

    try:
        return learn.predict(x)
    except Exception:
        print('ERROR get_prediction_by_uid')
        return 0


def get_prediction_graph_by_uid(uid: str):
    try:
        result = list()

        for i in predictions_db.get_predictions_by_uid(uid):
            result.append({
                'prediction': i[1],
                'date': i[2],
            })
            print(i)

        print(result)

        return result
    except Exception:
        print('ERROR get_prediction_graph_by_uid')
        return []
