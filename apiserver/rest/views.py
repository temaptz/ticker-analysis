import datetime
from rest_framework.decorators import api_view
from django.http import HttpResponse
from django.views.decorators.cache import cache_control
from tinkoff.invest import CandleInterval
from lib import serializer, instruments, forecasts, predictions, users, news, utils, fundamentals
import json


@api_view(['GET'])
@cache_control(public=True, max_age=3600 * 24 * 7)
def instruments_list(request):
    return HttpResponse(serializer.to_json(instruments.get_instruments_white_list()))


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
        consensus = forecasts.get_forecasts(uid).consensus

        if consensus:
            resp = serializer.get_dict_by_object(consensus)

    return HttpResponse(json.dumps(resp))


@api_view(['GET'])
def instrument_history_forecasts(request):
    resp = list()
    uid = request.GET.get('uid')

    if uid:
        for f in forecasts.get_db_forecasts_by_uid(uid=uid):
            forecast = f[1]
            date = f[2]

            resp.append({'time': date, 'consensus': serializer.get_dict_by_object(forecast.consensus)})

    return HttpResponse(json.dumps(resp))


@api_view(['GET'])
def instrument_fundamental(request):
    resp = list()
    uid = request.GET.get('asset_uid')

    if uid:
        fundamentals_resp = fundamentals.get_fundamentals_by_asset_uid(uid)

        if fundamentals_resp:
            for f in fundamentals_resp:
                resp = serializer.get_dict_by_object(f)

    return HttpResponse(json.dumps(resp))


@api_view(['GET'])
@cache_control(public=True, max_age=60)
def instrument_prediction(request):
    resp = None
    uid = request.GET.get('uid')

    if uid:
        resp = predictions.get_prediction_ta_1_by_uid(uid)

    return HttpResponse(json.dumps(resp))


@api_view(['GET'])
def instrument_prediction_graph(request):
    resp = None
    uid = request.GET.get('uid')

    if uid:
        resp = predictions.get_prediction_ta_1_graph_by_uid(uid)

    return HttpResponse(json.dumps(resp))


@api_view(['GET'])
@cache_control(public=True, max_age=60)
def instrument_balance(request):
    resp = None
    account_name = request.GET.get('account_name')
    uid = request.GET.get('uid')

    if account_name and uid:
        resp = users.get_user_instrument_balance(account_name=account_name, instrument_uid=uid)

    return HttpResponse(json.dumps(resp))


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
@cache_control(public=True, max_age=60)
def instrument_news(request):
    resp = None
    uid = request.GET.get('uid')
    start_date = utils.parse_json_date(request.GET.get('start_date'))
    end_date = utils.parse_json_date(request.GET.get('end_date'))

    if uid and start_date and end_date:
        resp = news.get_sorted_news_by_instrument_uid(instrument_uid=uid, start_date=start_date, end_date=end_date)

    return HttpResponse(serializer.to_json(resp))


@api_view(['GET'])
@cache_control(public=True, max_age=60)
def instrument_news_content_rated(request):
    resp = None
    uid = request.GET.get('uid')
    start_date = utils.parse_json_date(request.GET.get('start_date'))
    end_date = utils.parse_json_date(request.GET.get('end_date'))

    if uid and start_date and end_date:
        resp = news.get_sorted_rated_news_content_by_instrument_uid(instrument_uid=uid, start_date=start_date, end_date=end_date)

    return HttpResponse(serializer.to_json(resp))


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
