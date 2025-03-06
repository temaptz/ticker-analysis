import datetime
from rest_framework.decorators import api_view
from django.http import HttpResponse
from django.views.decorators.cache import cache_control
from django.utils.cache import patch_cache_control
from tinkoff.invest import CandleInterval, Instrument
from lib import serializer, instruments, forecasts, predictions, users, news, utils, fundamentals, counter, date_utils
import json


@api_view(['GET'])
@cache_control(public=True, max_age=3600 * 24 * 7)
def instruments_list_full(request):
    print('START REQUEST')
    resp = []

    for instrument in instruments.get_instruments_white_list():
        print(instrument.ticker)
        resp.append(get_instrument_full(instrument=instrument))

    print(counter.get_stat())

    return HttpResponse(serializer.to_json(resp))


@api_view(['GET'])
@cache_control(public=True, max_age=3600 * 24 * 7)
def instruments_list(request):
    return HttpResponse(serializer.to_json(instruments.get_instruments_white_list()))


@api_view(['GET'])
@cache_control(public=True, max_age=3600 * 24 * 7)
def instrument_info_full(request):
    resp = None
    uid = request.GET.get('uid')

    if uid:
        instrument = instruments.get_instrument_by_uid(uid)

        if instrument:
            resp = get_instrument_full(instrument=instrument)

    return HttpResponse(serializer.to_json(resp))


@api_view(['GET'])
@cache_control(public=True, max_age=3600 * 24 * 7)
def instrument_info(request):
    resp = ''
    uid = request.GET.get('uid')

    if uid:
        instrument = instruments.get_instrument_by_uid(uid)

        if instrument:
            resp = serializer.get_dict_by_object(instrument)

    return HttpResponse(json.dumps(resp))


@api_view(['GET'])
@cache_control(public=True, max_age=3600)
def instrument_last_prices(request):
    resp = list()
    uid = request.GET.get('uid')

    if uid:
        for i in instruments.get_instrument_last_price_by_uid(uid):
            resp.append(serializer.get_dict_by_object(i))

    return HttpResponse(json.dumps(resp))


@api_view(['GET'])
def instrument_price_by_date(request):
    uid = request.GET.get('uid')
    date = utils.parse_json_date(request.GET.get('date'))

    data = instruments.get_instrument_price_by_date(uid=uid, date=date)
    response = HttpResponse(data or json.dumps(None))

    if data:
        patch_cache_control(response, public=True, max_age=3600 * 24)

    return response


@api_view(['GET'])
@cache_control(public=True, max_age=3600)
def instrument_history_prices(request):
    resp = list()
    uid = request.GET.get('uid')
    days = request.GET.get('days')
    interval = request.GET.get('interval')

    if uid and days and interval:
        for i in instruments.get_instrument_history_price_by_uid(
                uid=uid,
                days_count=int(days),
                interval=CandleInterval(int(interval)),
                to_date=datetime.datetime.now()
        ):
            resp.append(serializer.get_dict_by_object(i))

    return HttpResponse(json.dumps(resp))


@api_view(['GET'])
def instrument_consensus_forecast(request):
    resp = ''
    uid = request.GET.get('uid')

    if uid:
        consensus = forecasts.get_forecasts(uid)

        if consensus:
            resp = serializer.get_dict_by_object(consensus.consensus)

    response = HttpResponse(json.dumps(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600 * 24 * 7)

    return response


@api_view(['GET'])
def instrument_history_forecasts(request):
    resp = list()
    uid = request.GET.get('uid')

    if uid:
        for f in forecasts.get_db_forecasts_by_uid(uid=uid):
            forecast = f[1]
            date = f[2]

            resp.append({'time': date, 'consensus': serializer.get_dict_by_object(forecast.consensus)})

    response = HttpResponse(json.dumps(resp))

    if len(resp):
        patch_cache_control(response, public=True, max_age=3600 * 24 * 7)

    return response


@api_view(['GET'])
def instrument_fundamental(request):
    resp = list()
    uid = request.GET.get('asset_uid')

    if uid:
        fundamentals_resp = fundamentals.get_fundamentals_by_asset_uid(uid)

        if fundamentals_resp:
            for f in fundamentals_resp:
                resp = serializer.get_dict_by_object(f)

    response = HttpResponse(json.dumps(resp))

    if len(resp):
        patch_cache_control(response, public=True, max_age=3600 * 24 * 7)

    return response


@api_view(['GET'])
def instrument_prediction(request):
    resp = None
    uid = request.GET.get('uid')

    if uid:
        resp = predictions.get_prediction_ta_1_by_uid(uid)

    response = HttpResponse(json.dumps(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600)

    return response


@api_view(['GET'])
def instrument_prediction_graph(request):
    resp = {}
    uid = request.GET.get('uid')
    date_from = date_utils.parse_date(request.GET.get('date_from'))
    date_to = date_utils.parse_date(request.GET.get('date_to'))
    interval = request.GET.get('interval')

    if uid and date_from and date_to and interval:
        resp['ta1'] = predictions.get_prediction_ta_1_graph_by_uid(
            uid=uid,
            date_from=date_from,
            date_to=date_to,
            interval=interval,
        )
    response = HttpResponse(json.dumps(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600 * 24 * 7)

    return response


@api_view(['GET'])
def instrument_balance(request):
    resp = None
    account_name = request.GET.get('account_name')
    uid = request.GET.get('uid')

    if account_name and uid:
        resp = users.get_user_instrument_balance(account_name=account_name, instrument_uid=uid)

    response = HttpResponse(json.dumps(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600)

    return response


@api_view(['GET'])
@cache_control(public=True, max_age=60)
def instrument_operations(request):
    resp = None
    account_name = request.GET.get('account_name')
    figi = request.GET.get('figi')

    if account_name and figi:
        resp = users.get_user_instrument_operations(account_name=account_name, instrument_figi=figi)

    return HttpResponse(serializer.to_json(resp))


@api_view(['GET'])
def instrument_news(request):
    resp = None
    uid = request.GET.get('uid')
    start_date = utils.parse_json_date(request.GET.get('start_date'))
    end_date = utils.parse_json_date(request.GET.get('end_date'))

    if uid and start_date and end_date:
        resp = news.get_sorted_news_count_by_instrument_uid(instrument_uid=uid, start_date=start_date, end_date=end_date)

    response = HttpResponse(serializer.to_json(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600 * 24 * 7)

    return response


@api_view(['GET'])
def instrument_news_content_rated(request):
    resp = None
    uid = request.GET.get('uid')
    start_date = utils.parse_json_date(request.GET.get('start_date'))
    end_date = utils.parse_json_date(request.GET.get('end_date'))

    if uid and start_date and end_date:
        resp = news.get_sorted_rated_news_content_by_instrument_uid(instrument_uid=uid, start_date=start_date, end_date=end_date)

    response = HttpResponse(serializer.to_json(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600 * 24 * 7)

    return response


@api_view(['GET'])
@cache_control(public=True, max_age=3600 * 24 * 30)
def instrument_brand(request):
    resp = None
    uid = request.GET.get('uid')

    if uid:
        instrument = instruments.get_instrument_by_uid(uid=uid)

        if instrument:
            resp = instruments.get_instrument_by_ticker(ticker=instrument.ticker).brand

    return HttpResponse(serializer.to_json(resp))


def get_instrument_full(instrument: Instrument):
    return {
        'instrument': instruments.get_instrument_by_uid(uid=instrument.uid),
        'current_price': instruments.get_instrument_price_by_date(uid=instrument.uid, date=datetime.datetime.now()),
        'history_5_years': instruments.get_instrument_history_price_by_uid(
            uid=instrument.uid,
            days_count=365 * 5,
            interval=CandleInterval.CANDLE_INTERVAL_MONTH,
            to_date=datetime.datetime.now()
        ),
        'history_1_year': instruments.get_instrument_history_price_by_uid(
            uid=instrument.uid,
            days_count=365,
            interval=CandleInterval.CANDLE_INTERVAL_WEEK,
            to_date=datetime.datetime.now()
        ),
        'history_90_days': instruments.get_instrument_history_price_by_uid(
            uid=instrument.uid,
            days_count=90,
            interval=CandleInterval.CANDLE_INTERVAL_DAY,
            to_date=datetime.datetime.now()
        ),
        'forecast': getattr(getattr(
            forecasts.get_forecasts(instrument_uid=instrument.uid),
            'consensus',
            {}
        ), 'consensus', None),
        'forecast_history': forecasts.get_db_forecasts_by_uid(uid=instrument.uid),
        'fundamentals': fundamentals.get_fundamentals_by_asset_uid(asset_uid=instrument.asset_uid),
        'prediction_ta1': predictions.get_prediction_ta_1_by_uid(uid=instrument.uid),
        'prediction_ta1_graph': predictions.get_prediction_ta_1_graph_by_uid(uid=instrument.uid),
        'balance_main': users.get_user_instrument_balance(
            account_name='Основной',
            instrument_uid=instrument.uid,
        ),
        'balance_analytics': users.get_user_instrument_balance(
            account_name='Аналитический',
            instrument_uid=instrument.uid,
        ),
        'operations_main': users.get_user_instrument_operations(
            account_name='Основной',
            instrument_figi=instrument.figi,
        ),
        'operations_analytics': users.get_user_instrument_operations(
            account_name='Аналитический',
            instrument_figi=instrument.figi,
        ),
        'news_week_0': news.get_sorted_news_count_by_instrument_uid(
            instrument_uid=instrument.uid,
            start_date=datetime.datetime.now() - datetime.timedelta(days=7),
            end_date=datetime.datetime.now()
        ),
        'news_week_1': news.get_sorted_news_count_by_instrument_uid(
            instrument_uid=instrument.uid,
            start_date=datetime.datetime.now() - datetime.timedelta(days=14),
            end_date=datetime.datetime.now() - datetime.timedelta(days=8)
        ),
        'brand': instruments.get_instrument_by_ticker(ticker=instrument.ticker).brand
    }
