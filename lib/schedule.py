from apscheduler.schedulers.blocking import BlockingScheduler
import pytz
from lib import forecasts_save, predictions_save, yandex_disk, process_task, fundamentals_save, news


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
        hour=11,
        minute=0,
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

    # Инвестиционные рекомендации
    # scheduler.add_job(
    #     process_task.send_invest_recommendations,
    #     'cron',
    #     day_of_week='mon',
    #     day_of_month=1,
    #     hour=15,
    #     minute=0,
    #     timezone=timezone
    # )

    # Проверка сообщений в телеге
    scheduler.add_job(
        process_task.process_updates,
        'interval',
        seconds=30
    )

    scheduler.start()
