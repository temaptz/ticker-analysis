from lib.db_2 import forecasts_db
from lib import telegram, instruments, forecasts, serializer


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
                instrument_uid=instrument.uid,
                forecast=f
            )

            counter += 1

    telegram.send_message('Всего сохранено '+str(counter)+' прогнозов аналитиков')


def show_saved_forecasts():
    for f in forecasts_db.get_forecasts():
        uid = f.instrument_uid
        date = f.date
        data = serializer.db_deserialize(f.forecasts)
        print(uid)
        print(date)
        print(data)
