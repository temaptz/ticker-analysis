import datetime
from lib.db_2 import fundamentals_db
from lib import telegram, instruments, fundamentals


def save_fundamentals():
    telegram.send_message('Начато сохранение фундаментальных показателей')

    counter = 0

    for instrument in instruments.get_instruments_white_list():
        print(instrument.ticker)
        print(instrument.name)

        for f in fundamentals.get_fundamentals_by_asset_uid(asset_uid=instrument.asset_uid) or []:
            print('FUNDAMENTALS SAVE', f)

            fundamentals_db.insert_fundamentals(
                asset_uid=instrument.asset_uid,
                fundamental=f
            )

            counter += 1

    telegram.send_message('Всего сохранено '+str(counter)+' фундаментальных показателей')


def show_saved():
    for instrument in instruments.get_instruments_white_list():
        print(instrument.ticker)
        print(instrument.name)

        now = datetime.datetime.now()
        past_week = now - datetime.timedelta(weeks=1)

        saved_past_week = fundamentals.get_db_fundamentals_by_asset_uid_date(asset_uid=instrument.asset_uid, date=past_week)
        saved_last = fundamentals.get_db_fundamentals_by_asset_uid_date(asset_uid=instrument.asset_uid, date=now)

        print('FUNDAMENTALS SAVED PAST WEEK', saved_past_week)
        print('FUNDAMENTALS SAVED LAST', saved_last)
