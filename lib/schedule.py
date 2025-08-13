import datetime
import time
import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
from lib import forecasts_save, predictions_save, yandex_disk, process_task, fundamentals_save, news, agent, logger, telegram, schedule_llm


def start_schedule() -> None:
    timezone = pytz.timezone('Europe/Moscow')
    scheduler = BlockingScheduler()

    # Сбор фундаментальных показателей
    scheduler.add_job(
        fundamentals_save.save_fundamentals,
        'cron',
        day_of_week='mon',
        hour=10,
        minute=0,
        timezone=timezone
    )

    # Сбор прогнозов аналитиков
    scheduler.add_job(
        forecasts_save.save_forecasts,
        'cron',
        day_of_week='mon',
        hour=10,
        minute=20,
        timezone=timezone
    )

    # Ежедневный сбор предсказаний нейросети
    scheduler.add_job(
        predictions_save.save_daily_predictions,
        'cron',
        hour=13,
        minute=0,
        timezone=timezone
    )

    # Еженедельный сбор предсказаний нейросети
    scheduler.add_job(
        predictions_save.save_weekly_predictions,
        'cron',
        day_of_week='mon',
        hour=14,
        minute=0,
        timezone=timezone
    )

    # Сбор свежих новостей
    scheduler.add_job(
        news.news_save.save_news,
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

    schedule_llm.register_scheduler_jobs(scheduler=scheduler)

    scheduler.start()
