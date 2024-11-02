import datetime
import tinkoff.invest
import os
import sys
from serializer import get_dict_by_object
import forecasts_db
import forecasts_db
from learning_card import LearningCard
import learn


def get_prediction_by_uid(uid: str) -> float:
    c = LearningCard()
    c.load_by_uid(uid=uid)
    x = c.get_x()

    prediction = learn.predict(x)

    return prediction
