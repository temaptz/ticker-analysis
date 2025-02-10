from apscheduler.schedulers.blocking import BlockingScheduler
import pytz

from lib import (
    forecasts_save,
    predictions_save,
    news_save,
    yandex_disk,
    telegram,
)


def start_schedule() -> None:
    timezone = pytz.timezone('Europe/Moscow')
    scheduler = BlockingScheduler()

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

    # Проверка сообщений в телеге
    scheduler.add_job(
        telegram.process_updates,
        'interval',
        seconds=30
    )

    scheduler.start()
