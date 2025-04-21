import datetime
from collections import defaultdict
from tinkoff.invest import Client, constants, CandleInterval
from tinkoff.invest.schemas import GetForecastResponse, GetForecastRequest
from lib.db_2 import forecasts_db
from const import TINKOFF_INVEST_TOKEN
from lib import cache, utils, serializer


@cache.ttl_cache(ttl=3600 * 24 * 3)
def get_forecasts(instrument_uid: str) -> GetForecastResponse:
    try:
        with Client(token=TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.instruments.get_forecast_by(
                request=GetForecastRequest(
                    instrument_id=instrument_uid
                )
            )

    except Exception as e:
        print('ERROR GETTING FORECASTS OF: ', instrument_uid, e)


@cache.ttl_cache(ttl=3600 * 24 * 3)
def get_db_forecast_by_uid_date(uid: str, date: datetime.datetime) -> (str, GetForecastResponse, str):
    db_resp = forecasts_db.get_forecast_by_uid_date(uid=uid, date=date)
    uid = db_resp.instrument_uid
    date = db_resp.date
    forecast = serializer.db_deserialize(db_resp.forecasts)

    return uid, forecast, date


@cache.ttl_cache(ttl=3600 * 24 * 3)
def get_db_forecasts_graph(
        instrument_uid: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        interval: CandleInterval = CandleInterval.CANDLE_INTERVAL_DAY
):
    result = list()

    try:
        for f in forecasts_db.get_forecasts_by_uid_date(
                instrument_uid=instrument_uid,
                start_date=start_date,
                end_date=end_date,
        ):
            result.append({
                'date': utils.parse_json_date(f.date),
                'consensus': utils.get_price_by_quotation(serializer.db_deserialize(f.forecasts).consensus.consensus)
            })

    except Exception as e:
        print('ERROR get_db_forecasts_graph', e)

    return utils.filter_array_by_date_interval(source=result, date_field='date', interval=interval)


@cache.ttl_cache(ttl=3600 * 24 * 3)
def get_db_forecasts_history_by_uid(uid: str) -> (str, GetForecastResponse, str):
    result = list()

    try:
        for f in forecasts_db.get_forecasts_by_uid(uid=uid):
            result.append({
                'date': utils.parse_json_date(f.date),
                'consensus': serializer.db_deserialize(f.forecasts).consensus
            })

        result = filter_monthly(result)
    except Exception as e:
        print('ERROR get_db_forecasts_history_by_uid', e)

    return result


def filter_monthly(resp):
    # Проверяем, не пуст ли входной список
    if not resp:
        return []

    # Определяем текущие год и месяц по системному времени
    now = datetime.datetime.now()
    current_year_month = (now.year, now.month)

    # Готовим структуру для группировки: ключ – (год, месяц), значение – список записей
    groups = defaultdict(list)
    for item in resp:
        d = item['date']
        # Убеждаемся, что дата имеет тип datetime.datetime
        if not isinstance(d, datetime.datetime):
            raise ValueError('item[\'date\'] must be a datetime.datetime')
        # Добавляем текущую запись в соответствующую группу
        groups[(d.year, d.month)].append(item)

    filtered = []
    # Проходим по сгруппированным записям помесячно
    for (year, month), items in groups.items():
        # Сортируем записи внутри месяца по дате возрастанию
        items_sorted = sorted(items, key=lambda x: x['date'])
        # Если это текущий (последний) месяц
        if (year, month) == current_year_month:
            # Берем первую (самую раннюю) и, при необходимости, последнюю
            earliest = items_sorted[0]
            latest = items_sorted[-1]
            filtered.append(earliest)
            # Если первая и последняя отличаются
            if earliest['date'] != latest['date']:
                filtered.append(latest)
        else:
            # Для остальных месяцев берем только самую раннюю запись
            filtered.append(items_sorted[0])

    # Сортируем все отфильтрованные записи в порядке убывания дат (сначала самые свежие)
    filtered.sort(key=lambda x: x['date'], reverse=True)
    return filtered
