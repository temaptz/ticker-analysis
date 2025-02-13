from lib.db import forecasts_db
from lib import telegram, instruments, forecasts


def save_forecasts():
    telegram.send_message('Начато сохранение прогнозов аналитиков')

    counter = 0

    for instrument in instruments.get_instruments_white_list():
        print(instrument.ticker)
        print(instrument.name)

        f = forecasts.get_forecasts(instrument_uid=instrument.uid)
        if f:
            print('FORECASTS')
            for i in f.targets:
                print(i)

            print('CONSENSUS FORECASTS')
            print(f.consensus)

            forecasts_db.insert_forecast(
                uid=instrument.uid,
                forecast=forecasts_db.serialize(f)
            )

            counter += 1

    telegram.send_message('Всего сохранено '+str(counter)+' прогнозов аналитиков')


def show_saved_forecasts():
    for f in forecasts_db.get_forecasts():
        uid = f[0]
        date = f[2]
        data = forecasts_db.deserialize(f[1])
        print(uid)
        print(date)
        print(data)
