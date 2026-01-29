from __future__ import annotations

import datetime
import os
import time
import signal
import multiprocessing as mp
from typing import Optional, Dict

import pytz
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import find_dotenv

from lib import agent, logger, telegram

# === НАСТРОЙКИ ВРЕМЕНИ ===
TZ = pytz.timezone('Europe/Moscow')

# === РЕЕСТР ЗАПУЩЕННЫХ ДОЛГИХ ПРОЦЕССОВ ===
# Ключи: 'RECS', 'NEWS_WEEKDAY'
RUNNING: Dict[str, Optional[mp.Process]] = {'RECS': None, 'NEWS_WEEKDAY': None}


dotenv_path = find_dotenv()

def _load_worker_env():
    from dotenv import load_dotenv
    from langsmith import utils as _ls_utils
    load_dotenv(dotenv_path=dotenv_path, override=True)
    _ls_utils.get_env_var.cache_clear()
    os.environ.setdefault('LANGCHAIN_CALLBACKS_BACKGROUND', 'false')

_load_worker_env()


def _now() -> datetime.datetime:
    return datetime.datetime.now(TZ)


def _next_weekday_cutoff_10() -> datetime.datetime:
    """Возвращает ближайший дедлайн 10:00 следующего буднего дня.
    Например, если сейчас вт 11:15 - дедлайн будет ср 10:00.
    Если сегодня пт 12:00 - дедлайн будет пн 10:00.
    """
    now = _now()
    d = now
    # шаг до следующего дня
    d = d + datetime.timedelta(days=1)
    # Прокрутим до ближайшего буднего дня (0=Пн..6=Вс)
    while d.weekday() >= 5:  # 5=Сб, 6=Вс
        d = d + datetime.timedelta(days=1)
    return d.replace(hour=10, minute=0, second=0, microsecond=0)


def _next_monday_10() -> datetime.datetime:
    now = _now()
    # 0=Пн..6=Вс, надо добраться до Пн
    days_ahead = (0 - now.weekday()) % 7
    target = (now + datetime.timedelta(days=days_ahead)).replace(hour=10, minute=0, second=0, microsecond=0)
    if target <= now:
        target = target + datetime.timedelta(days=7)
    return target


def _get_deadline():
    wd = _now().weekday()
    return _next_monday_10() if wd == 4 else _next_weekday_cutoff_10()


def _start_proc(name: str, target, *args, **kwargs) -> Optional[mp.Process]:
    p = RUNNING.get(name)
    if p and p.is_alive():
        print(f'[SKIP] {name} уже запущен (pid={p.pid})')
        return p
    p = mp.Process(
        target=target,
        name=name,
        args=args,
        kwargs=kwargs,
        daemon=True,
    )
    p.start()
    RUNNING[name] = p
    print(f'[START] {name} pid={p.pid}')
    return p


def _kill_proc(name: str, reason: str) -> None:
    p = RUNNING.get(name)
    if p and p.is_alive():
        print(f'[KILL] {name} pid={p.pid} - причина: {reason}')
        try:
            # сначала мягко
            p.terminate()
            p.join(timeout=30)
            if p.is_alive():
                # жёсткая остановка
                os.kill(p.pid, signal.SIGKILL)
                p.join(timeout=5)
        except Exception as e:
            logger.log_error(method_name=f'kill_{name}', error=e)
    RUNNING[name] = None


def _worker_news_loop(deadline_ts: float) -> None:
    """Цикл оценки новостей до дедлайна. В будни - до ближайших 10:00, на выходных - до пн 10:00."""
    deadline = datetime.datetime.fromtimestamp(deadline_ts, tz=TZ)
    telegram.send_message('Старт оценки новостей')
    try:
        while _now() < deadline:
            try:
                agent.news_rank.rank_last_news()
            except Exception as e:
                logger.log_error(method_name='rank_last_news', error=e)
            # Пауза между итерациями, чтобы не крутить слишком часто
            time.sleep(5)
    finally:
        telegram.send_message('Завершение оценки новостей')


def _worker_update_recommendations(deadline_ts: float) -> None:
    """Обновление рекомендаций до дедлайна. Если не успеет - будет убит снаружи в 10:00."""
    try:
        telegram.send_message('Старт обновления рекомендаций')
        agent.instrument_rank_sell.update_recommendations()
        agent.instrument_rank_buy.update_recommendations()
    except Exception as e:
        logger.log_error(method_name='update_recommendations', error=e)
    finally:
        telegram.send_message('Завершено обновление рекомендаций')

    _worker_news_loop(deadline_ts)


def weekday_11_pipeline() -> None:
    """Будничный цикл: 11:00 - создать заявки, затем старт длинной задачи по дню недели."""
    # На всякий случай, перед началом чистим возможные хвосты
    _kill_proc('RECS', 'weekday-11-start')
    _kill_proc('NEWS_WEEKDAY', 'weekday-11-start')

    # 2) Ветка в зависимости от дня
    wd = _now().weekday()  # 0=Пн..6=Вс
    deadline = _get_deadline()
    deadline_ts = deadline.timestamp()

    if wd in (0, 1, 2, 3, 4):  # Пн-Пт - рекомендации
        _start_proc('RECS', _worker_update_recommendations, deadline_ts)
    else:
        _start_proc('NEWS_WEEKDAY', _worker_news_loop, deadline_ts)


def daily_cutoff_10() -> None:
    """Каждый будний день 10:00 - принудительно останавливаем длинные задачи для часа отдыха."""
    _kill_proc('RECS', 'daily-cutoff-10')
    _kill_proc('NEWS_WEEKDAY', 'daily-cutoff-10')


def register_scheduler_jobs(scheduler: BaseScheduler):
    # 10:00 по будням - принудительный стоп
    scheduler.add_job(
        daily_cutoff_10,
        CronTrigger(day_of_week='mon-fri', hour=10, minute=30, timezone=TZ),
        id='daily_cutoff_10',
        replace_existing=True,
    )

    # 11:00 по будням - запуск конвейера
    scheduler.add_job(
        weekday_11_pipeline,
        CronTrigger(day_of_week='mon-fri', hour=11, minute=0, timezone=TZ),
        id='weekday_11_pipeline',
        replace_existing=True,
    )


def start_available_job():
    if _now().hour != 10:
        print('LLM START AVAILABLE JOB')

        deadline = _get_deadline()

        if deadline > _now():
            logger.log_info(message='Начало выполнения LLM задач')

            deadline_ts = deadline.timestamp()
            # _start_proc('RECS', _worker_update_recommendations, deadline_ts)
            _start_proc('NEWS_WEEKDAY', _worker_news_loop, deadline_ts)
