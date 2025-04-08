from apscheduler.schedulers.blocking import BlockingScheduler
import pytz
from lib import forecasts_save, predictions_save, news_save, yandex_disk, process_task, fundamentals_save


def start_schedule() -> None:
    timezone = pytz.timezone('Europe/Moscow')
    scheduler = BlockingScheduler()

    # Сбор прогнозов аналитиков
    scheduler.add_job(
        forecasts_save.save_forecasts,
        'cron',
        day_of_week='mon',
        hour=13,
        minute=0,
        timezone=timezone
    )

    # Сбор фундаментальных показателей
    scheduler.add_job(
        fundamentals_save.save_fundamentals,
        'cron',
        day_of_week='mon',
        hour=14,
        minute=0,
        timezone=timezone
    )

    # Сбор предсказаний нейросети
    scheduler.add_job(
        predictions_save.save_predictions,
        'cron',
        hour=11,
        minute=0,
        timezone=timezone
    )

    # Сбор свежих новостей
    scheduler.add_job(
        news_save.save_news,
        'cron',
        hour='*/3',
        minute=0,
        timezone=timezone
    )

    # Резервное копирование БД
    scheduler.add_job(
        yandex_disk.upload_db_backup,
        'cron',
        hour=5,
        minute=0,
        timezone=timezone
    )

    # Проверка сообщений в телеге
    scheduler.add_job(
        process_task.process_updates,
        'interval',
        seconds=30
    )

    scheduler.start()
