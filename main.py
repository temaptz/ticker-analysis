from apscheduler.schedulers.blocking import BlockingScheduler
import pytz

from lib import (
    forecasts_save,
    predictions_save,
    news_save,
    telegram,
    docker,
    yandex_disk
)

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


if docker.is_docker():
    telegram.send_message('Скрипт ticker-analysis main запущен')

    # Сбор прогнозов аналитиков
    scheduler.add_job(
        forecasts_save.save_favorite_forecasts,
        'cron',
        day_of_week='mon',
        hour=12,
        minute=0,
        timezone=timezone
    )

    # Сбор предсказаний нейросети
    scheduler.add_job(
        predictions_save.save_favorite_predictions,
        'cron',
        hour=11,
        minute=0,
        timezone=timezone
    )

    # Сбор свежих новостей
    scheduler.add_job(
        news_save.save_news,
        'cron',
        minute=0,
        timezone=timezone
    )

    # Резервное копирование БД
    scheduler.add_job(
        yandex_disk.upload_db_backup,
        'cron',
        day_of_week='fri',
        hour=15,
        minute=30,
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
