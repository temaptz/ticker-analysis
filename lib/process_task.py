from lib import cache, yandex_disk, forecasts_save, predictions_save, fundamentals_save, docker, counter, redis_utils, telegram, news, agent, logger, users
from lib.db_2 import db_utils


def process_updates() -> None:
    cache_key = 'telegram_offset_update_id'
    offset_update_id = cache.cache_get(cache_key)
    updates = telegram.get_updates(offset_update_id=offset_update_id)
    for u in updates:
        update_id = u['update_id']
        if text := (u.get('message', {}).get('text') or  '').lower():
            cache.cache_set(cache_key, update_id)
            if update_id != offset_update_id:
                print('TELEGRAM UPDATE_ID', update_id)
                print('TELEGRAM UPDATE_TEXT', text)
                process_single_update(text)


def process_single_update(text: str = None) -> None:
    print('PROCESS TELEGRAM TASK', text)

    if text == '/backup':
        yandex_disk.upload_db_backup()

    elif text == '/forecasts':
        forecasts_save.save_forecasts()

    elif text == '/fundamentals':
        fundamentals_save.save_fundamentals()

    elif text == '/predictions':
        predictions_save.save_weekly_predictions()

    elif text == '/news':
        news.news_save.save_news()

    elif text == '/optimize':
        telegram.send_message('Начало оптимизации БД')
        db_utils.optimize_db()

    elif text == '/stat':
        telegram.send_message('Сбор статистики')
        telegram.send_message('uptime')
        telegram.send_message(docker.get_uptime())
        telegram.send_message('df -h')
        telegram.send_message(docker.get_df())
        telegram.send_message('Счетчики')
        telegram.send_message(counter.get_stat())
        telegram.send_message('Статистика redis')
        telegram.send_message(redis_utils.get_redis_stats())

    elif text == '/cache':
        telegram.send_message('Очистка кэша')
        cache.clean()

    elif text == '/recommendation':
        telegram.send_message(message='Отключено')

    elif text == '/trade':
        telegram.send_message(message='Создание торговых заявок через телегу отключено')
        # agent.sell.create_orders()
        # agent.buy.create_orders()


# def buy_sell_rate() -> None:
#     try:
#         agent.instrument_rank_sell.update_recommendations()
#         agent.instrument_rank_buy.update_recommendations()
#     except Exception as e:
#         logger.log_error(method_name='create_orders', error=e)


def create_orders() -> None:
    try:
        agent.sell.create_orders_3(account_id=users.get_analytics_account().id)
        agent.buy.create_orders_3(account_id=users.get_analytics_account().id)
    except Exception as e:
        logger.log_error(method_name='create_orders', error=e)