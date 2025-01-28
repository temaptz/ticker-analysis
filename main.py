from apscheduler.schedulers.blocking import BlockingScheduler
import pytz

from lib import (
    forecasts_save,
    predictions_save,
    news_save
)
from lib import telegram

# import instruments
# import prices
# import statistic
# import prepare_data
# import learn

timezone = pytz.timezone('Europe/Moscow')
scheduler = BlockingScheduler()

tg_updates = telegram.get_updates()
print('TELEGRAM UPDATES')
print(tg_updates)

telegram.send_message('Скрипт ticker-analysis main запущен')


# Сбор прогнозов аналитиков
def job_forecasts():
    telegram.send_message('Начато выполнение задания: collect-forecasts')
    forecasts_save.save_favorite_forecasts()


# Сбор предсказаний нейросети
def job_predictions():
    telegram.send_message('Начато выполнение задания: collect-predictions')
    predictions_save.save_favorite_predictions()


# Сбор свежих новостей
def job_news():
    telegram.send_message('Начато выполнение задания: collect-news')
    news_save.save_news()


scheduler.add_job(
    job_forecasts,
    'cron',
    day_of_week='mon',
    hour=12,
    minute=0,
    timezone=timezone
)

scheduler.add_job(
    job_predictions,
    'cron',
    hour=11,
    minute=0,
    timezone=timezone
)

scheduler.add_job(
    job_news,
    'cron',
    minute=0,
    timezone=timezone
)

scheduler.start()

# instruments.show_instruments()
# prices.show_prices()
# statistic.collect()
# prepare_data.show()
# prepare_data.prepare_cards()
# prepare_data.get_saved()
# learn.learn()
