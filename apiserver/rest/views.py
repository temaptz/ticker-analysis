import datetime
from rest_framework.decorators import api_view
from django.http import HttpResponse
from tinkoff.invest import (
    CandleInterval
)
from lib import serializer, instruments, forecasts, predictions, users
import json


@api_view(['GET'])
def instruments_list(request):
    resp = list()

    for i in instruments.get_favorites():
        resp.append(serializer.get_dict_by_object(i))

    return HttpResponse(json.dumps(resp))

@api_view(['GET'])
def instrument_info(request):
    resp = ''
    uid = request.GET.get('uid')

    if uid:
        instrument = instruments.get_instrument_by_uid(uid)

        if instrument:
            resp = serializer.get_dict_by_object(instrument)

    return HttpResponse(json.dumps(resp))


@api_view(['GET'])
def instrument_last_prices(request):
    resp = list()
    uid = request.GET.get('uid')

    if uid:
        for i in instruments.get_instrument_last_price_by_uid(uid):
            resp.append(serializer.get_dict_by_object(i))

    return HttpResponse(json.dumps(resp))


@api_view(['GET'])
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
        fc = instruments.get_instrument_consensus_forecast_by_uid(uid)

        if fc:
            resp = serializer.get_dict_by_object(fc)

    return HttpResponse(json.dumps(resp))


@api_view(['GET'])
def instrument_history_forecasts(request):
    resp = list()
    uid = request.GET.get('uid')

    if uid:
        fc = forecasts.get_db_forecasts_by_uid(uid=uid)

        for f in fc:
            forecast = f[1]
            date = f[2]

            resp.append({'time': date, 'consensus': serializer.get_dict_by_object(forecast.consensus)})

    return HttpResponse(json.dumps(resp))


@api_view(['GET'])
def instrument_fundamental(request):
    resp = list()
    uid = request.GET.get('asset_uid')

    if uid:
        fundamentals = instruments.get_instrument_fundamentals_by_asset_uid(uid)

        if fundamentals:
            for f in fundamentals:
                resp = serializer.get_dict_by_object(f)

    return HttpResponse(json.dumps(resp))


@api_view(['GET'])
def instrument_prediction(request):
    resp = None
    uid = request.GET.get('uid')

    if uid:
        resp = predictions.get_prediction_by_uid(uid)

    return HttpResponse(json.dumps(resp))


@api_view(['GET'])
def instrument_prediction_graph(request):
    resp = None
    uid = request.GET.get('uid')

    if uid:
        resp = predictions.get_prediction_graph_by_uid(uid)

    return HttpResponse(json.dumps(resp))


@api_view(['GET'])
def instrument_balance(request):
    resp = None
    account_name = request.GET.get('account_name')
    uid = request.GET.get('uid')

    if account_name and uid:
        resp = users.get_user_instrument_balance(account_name=account_name, instrument_uid=uid)

    return HttpResponse(json.dumps(resp))


@api_view(['GET'])
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

    if uid:
        resp = instrument_news.get_sorted_news_by_instrument_uid_by_source(uid=uid)

    return HttpResponse(serializer.to_json(resp))
