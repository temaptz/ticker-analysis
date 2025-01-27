from apscheduler.schedulers.blocking import BlockingScheduler
import pytz

from lib import (
    forecasts_save,
    predictions_save,
    news_save
)
from lib import sound

# import instruments
# import prices
# import statistic
# import prepare_data
# import learn

timezone = pytz.timezone('Europe/Moscow')
scheduler = BlockingScheduler()


# Сбор прогнозов аналитиков
def job_forecasts():
    sound.play_file('./sounds/collect-forecasts.mp3')
    forecasts_save.save_favorite_forecasts()


# Сбор предсказаний нейросети
def job_predictions():
    sound.play_file('./sounds/collect-predictions.mp3')
    predictions_save.save_favorite_predictions()


# Сбор свежих новостей
def job_news():
    sound.play_file('./sounds/collect-news.mp3')
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
