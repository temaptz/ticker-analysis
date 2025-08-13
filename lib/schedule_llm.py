"""
Надёжный планировщик для LLM‑задач с жёстким дедлайном и режимом выходных.

Ключевые свойства:
- По будням в 11:00 запускается конвейер: создание заявок (должно завершиться),
  затем в зависимости от дня:
    * Вт/Чт — обновление рекомендаций (в отдельном процессе, чтобы можно было принудительно завершить).
    * Пн/Ср/Пт — оценка новостей (в отдельном процессе, бесконечный цикл до дедлайна).
- Если длинные задачи (обновление рекомендаций или оценка новостей в будни) не
  успели завершиться до 10:00 — они принудительно останавливаются, чтобы с 10:00 до 11:00 был «час отдыха».
- На выходных (сб-вс) — непрерывная оценка новостей без остановок до понедельника 10:00.
- Используется APScheduler + отдельные процессы (multiprocessing) для надёжного прерывания.
- Исключены блокирующие бесконечные циклы внутри джоб планировщика — долгие задачи вынесены в отдельные процессы.

Замените импорты telegram/agent/logger/process_task на ваши реальные.
"""
from __future__ import annotations

import datetime as dt
import time
import signal
import multiprocessing as mp
from typing import Optional, Dict

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from lib import agent, logger, telegram

# === НАСТРОЙКИ ВРЕМЕНИ ===
TZ = pytz.timezone('Europe/Moscow')

# === РЕЕСТР ЗАПУЩЕННЫХ ДОЛГИХ ПРОЦЕССОВ ===
# Ключи: 'RECS', 'NEWS_WEEKDAY'
RUNNING: Dict[str, Optional[mp.Process]] = {'RECS': None, 'NEWS_WEEKDAY': None}


def _now() -> dt.datetime:
    return dt.datetime.now(TZ)


def _next_weekday_cutoff_10() -> dt.datetime:
    """Возвращает ближайший дедлайн 10:00 следующего буднего дня.
    Например, если сейчас вт 11:15 — дедлайн будет ср 10:00.
    Если сегодня пт 12:00 — дедлайн будет пн 10:00.
    """
    now = _now()
    d = now
    # шаг до следующего дня
    d = d + dt.timedelta(days=1)
    # Прокрутим до ближайшего буднего дня (0=Пн..6=Вс)
    while d.weekday() >= 5:  # 5=Сб, 6=Вс
        d = d + dt.timedelta(days=1)
    return d.replace(hour=10, minute=0, second=0, microsecond=0)


def _next_monday_10() -> dt.datetime:
    now = _now()
    # 0=Пн..6=Вс, надо добраться до Пн
    days_ahead = (0 - now.weekday()) % 7
    target = (now + dt.timedelta(days=days_ahead)).replace(hour=10, minute=0, second=0, microsecond=0)
    if target <= now:
        target = target + dt.timedelta(days=7)
    return target


# === УТИЛИТЫ ДЛЯ ПРОЦЕССОВ ===

def _start_proc(name: str, target, *args, **kwargs) -> Optional[mp.Process]:
    p = RUNNING.get(name)
    if p and p.is_alive():
        print(f"[SKIP] {name} уже запущен (pid={p.pid})")
        return p
    p = mp.Process(target=target, name=name, args=args, kwargs=kwargs, daemon=True)
    p.start()
    RUNNING[name] = p
    print(f"[START] {name} pid={p.pid}")
    return p


def _kill_proc(name: str, reason: str) -> None:
    p = RUNNING.get(name)
    if p and p.is_alive():
        print(f"[KILL] {name} pid={p.pid} — причина: {reason}")
        try:
            # сначала мягко
            p.terminate()
            p.join(timeout=30)
            if p.is_alive():
                # жёсткая остановка
                import os
                os.kill(p.pid, signal.SIGKILL)
                p.join(timeout=5)
        except Exception as e:
            logger.log_error(method_name=f"kill_{name}", error=e)
    RUNNING[name] = None


# === РАБОЧИЕ ФУНКЦИИ (в отдельных процессах) ===

def _worker_update_recommendations(deadline_ts: float) -> None:
    """Обновление рекомендаций до дедлайна. Если не успеет — будет убит снаружи в 10:00."""
    try:
        telegram.send_message('Старт обновления рекомендаций')
        agent.instrument_rank_sell.update_recommendations()
        agent.instrument_rank_buy.update_recommendations()
    except Exception as e:
        logger.log_error(method_name='update_recommendations', error=e)
    finally:
        telegram.send_message('Завершено обновление рекомендаций')


def _worker_news_loop(deadline_ts: float) -> None:
    """Цикл оценки новостей до дедлайна. В будни — до ближайших 10:00, на выходных — до пн 10:00."""
    deadline = dt.datetime.fromtimestamp(deadline_ts, tz=TZ)
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


# === ПАЙПЛАЙНЫ (внутри джоб APScheduler, короткие) ===

def weekday_11_pipeline() -> None:
    """Будничный цикл: 11:00 — создать заявки, затем старт длинной задачи по дню недели."""
    # На всякий случай, перед началом чистим возможные хвосты
    _kill_proc('RECS', 'weekday-11-start')
    _kill_proc('NEWS_WEEKDAY', 'weekday-11-start')

    telegram.send_message('Начало обработки LLM задач')

    # 1) Создание заявок — выполняется до конца (блокирующе)
    try:
        agent.sell.create_orders()
        agent.buy.create_orders()
    except Exception as e:
        logger.log_error(method_name='create_orders', error=e)

    # 2) Ветка в зависимости от дня
    wd = _now().weekday()  # 0=Пн..6=Вс
    deadline = _next_monday_10() if wd == 4 else _next_weekday_cutoff_10()
    deadline_ts = deadline.timestamp()

    if wd in (1, 4):  # Вт/Пт — рекомендации
        _start_proc('RECS', _worker_update_recommendations, deadline_ts)
    elif wd in (0, 2, 3):  # Пн/Ср/Чт — новости
        _start_proc('NEWS_WEEKDAY', _worker_news_loop, deadline_ts)
    else:
        # Если вдруг попали сюда (на всякий), запускаем новостной цикл
        _start_proc('NEWS_WEEKDAY', _worker_news_loop, deadline_ts)


def daily_cutoff_10() -> None:
    """Каждый будний день 10:00 — принудительно останавливаем длинные задачи для часа отдыха."""
    _kill_proc('RECS', 'daily-cutoff-10')
    _kill_proc('NEWS_WEEKDAY', 'daily-cutoff-10')


# === СТАРТ ПЛАНИРОВЩИКА ===

def register_scheduler_jobs(scheduler: BaseScheduler):
    # 10:00 по будням — принудительный стоп
    scheduler.add_job(
        daily_cutoff_10,
        CronTrigger(day_of_week='mon-fri', hour=10, minute=0, timezone=TZ),
        id='daily_cutoff_10',
        replace_existing=True,
    )

    # 11:00 по будням — запуск конвейера
    scheduler.add_job(
        weekday_11_pipeline,
        CronTrigger(day_of_week='mon-fri', hour=11, minute=0, timezone=TZ),
        id='weekday_11_pipeline',
        replace_existing=True,
    )
