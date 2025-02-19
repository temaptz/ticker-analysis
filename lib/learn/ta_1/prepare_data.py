import datetime
import time
from lib import instruments
from lib.db import learning_db
from lib.learn.ta_1.learning_card import LearningCard
import numpy


def prepare_cards():
    # learning_db.init_table()
    forecast_days = 30
    i = 0
    j = 0

    for uid in get_uids():
        for day in get_days(days=365, offset_days=forecast_days):
            print(i, uid, day)
            c = LearningCard()
            c.load(
                uid=uid,
                date=day,
                target_forecast_days=forecast_days
            )

            # c.print_card()

            if c.is_ok:
                learning_exists = learning_db.get_learning_by_uid_date(uid=c.uid, date=c.date)

                if len(learning_exists) == 0:
                    json_str = c.get_json_db()
                    learning_db.insert_learning(uid=c.uid, date=c.date, json=json_str)
                j += 1

            i += 1

            print('(total: '+str(i)+', is_ok: '+str(j)+')')

    # c = LearningCard(
    #     uid='ca845f68-6c43-44bc-b584-330d2a1e5eb7',
    #     date=(datetime.datetime.now() - datetime.timedelta(days=30)),
    #     target_forecast_days=forecast_days
    # )
    # c.print_card()


def get_saved() -> list[LearningCard]:
    result: list[LearningCard] = []

    for i in learning_db.get_learning():
        c = LearningCard()
        c.restore_from_json_db(json_data=i[2])

        if c.is_ok:
            result.append(c)

    return result


def get_saved_prepared_data():
    result = {
        'train_x': [],
        'train_y': [],
        'validate_x': [],
        'validate_y': [],
        'test_x': [],
        'test_y': [],
    }
    everything = get_saved()

    train, validate, test = numpy.split(everything, [int(len(everything)*0.8), int(len(everything)*0.9)])

    for i in train:
        result['train_x'].append(i.get_x())
        result['train_y'].append(i.get_y())

    for i in validate:
        result['validate_x'].append(i.get_x())
        result['validate_y'].append(i.get_y())

    for i in test:
        result['test_x'].append(i.get_x())
        result['test_y'].append(i.get_y())

    return result


def get_uids() -> list[str]:
    result = list[str]()

    for instrument in instruments.get_instruments_white_list():
        result.append(instrument.uid)

    return result


def get_days(days: int, offset_days: int) -> list[datetime.datetime]:
    result = list[datetime.datetime]()
    end_date = datetime.datetime.now().replace(hour=12, minute=0, second=0, microsecond=0) - datetime.timedelta(days=offset_days)

    for i in range(0, days):
        date = end_date - datetime.timedelta(days=i)
        result.append(date)

    return result
