import datetime
from rest_framework.decorators import api_view
from django.http import HttpResponse
from django.utils.cache import patch_cache_control
from tinkoff.invest import CandleInterval, Instrument, Quotation
from tinkoff.invest.schemas import IndicatorType, IndicatorInterval, Deviation, Smoothing

from lib import serializer, instruments, forecasts, predictions, users, news, utils, fundamentals, date_utils, invest_calc, tech_analysis
from lib.learn import ta_1_2, ta_2
import json


@api_view(['GET'])
def instruments_list(request):
    instruments_list_sorted = users.sort_instruments_by_balance(
        instruments_list=instruments.get_instruments_white_list()
    )

    response = HttpResponse(serializer.to_json(instruments_list_sorted))

    if len(instruments_list_sorted) != 0:
        patch_cache_control(response, public=True, max_age=3600 * 24 * 7)

    return response


@api_view(['GET'])
def instrument_info(request):
    resp = None
    uid = request.GET.get('uid')
    ticker = request.GET.get('ticker')
    instrument = None

    if uid:
        instrument = instruments.get_instrument_by_uid(uid)

    elif ticker:
        instrument = instruments.get_instrument_by_ticker(ticker)

    if instrument:
            resp = serializer.get_dict_by_object(instrument)

    response = HttpResponse(json.dumps(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600 * 24 * 7)

    return response


@api_view(['GET'])
def instrument_last_price(request):
    resp = None
    uid = request.GET.get('uid')

    if uid:
        last_price = instruments.get_instrument_last_price_by_uid(uid)

        if last_price is not None:
            resp = last_price

    response = HttpResponse(serializer.to_json(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600)

    return response


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

    response = HttpResponse(json.dumps(resp))

    if len(resp):
        patch_cache_control(response, public=True, max_age=3600 * 3)

    return response


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
        resp = forecasts.get_db_forecasts_history_by_uid(uid=uid)

    response = HttpResponse(serializer.to_json(resp))

    if len(resp) > 0:
        patch_cache_control(response, public=True, max_age=3600 * 24 * 7)

    return response


@api_view(['GET'])
def instrument_history_forecasts_graph(request):
    resp = list()
    uid = request.GET.get('uid')
    start_date = utils.parse_json_date(request.GET.get('start_date'))
    end_date = utils.parse_json_date(request.GET.get('end_date'))
    interval = CandleInterval(int(request.GET.get('interval')))

    if uid and start_date and end_date and interval:
        resp = forecasts.get_db_forecasts_graph(
            instrument_uid=uid,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
        )

    response = HttpResponse(serializer.to_json(resp))

    if resp and len(resp) > 0:
        patch_cache_control(response, public=True, max_age=3600 * 24 * 7)

    return response


@api_view(['GET'])
def instrument_fundamentals(request):
    resp = None
    asset_uid = request.GET.get('asset_uid')

    if asset_uid:
        fundamentals_resp = fundamentals.get_fundamentals_by_asset_uid(asset_uid=asset_uid)

        if fundamentals_resp:
            for f in fundamentals_resp:
                resp = serializer.get_dict_by_object(f)

    response = HttpResponse(json.dumps(resp))

    if len(resp):
        patch_cache_control(response, public=True, max_age=3600 * 24 * 7)

    return response


@api_view(['GET'])
def instrument_fundamentals_history(request):
    resp = list()
    asset_uid = request.GET.get('asset_uid')

    if asset_uid:
        resp = fundamentals.get_db_fundamentals_history_by_uid(asset_uid=asset_uid)

    response = HttpResponse(serializer.to_json(resp))

    if len(resp):
        patch_cache_control(response, public=True, max_age=3600 * 24 * 7)

    return response


@api_view(['GET'])
def instrument_prediction(request):
    resp = {}
    uid = request.GET.get('uid')

    if uid:
        next_month = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)
        resp['ta-1'] = predictions.get_prediction_ta_1_by_uid(uid)
        resp['ta-1_1'] = predictions.get_prediction_ta_1_1_by_uid(uid)
        resp['ta-1_2'] = ta_1_2.predict_future(instrument_uid=uid, date_target=next_month)
        resp['ta-2'] = ta_2.predict_future(instrument_uid=uid, date_target=next_month)
        resp['consensus'] = predictions.get_predictions_consensus(instrument_uid=uid, date_target=next_month)

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
    interval = CandleInterval(int(request.GET.get('interval')))

    if uid and date_from and date_to and interval:
        resp['ta-1'] = predictions.get_prediction_ta_1_graph(
            uid=uid,
            date_from=date_from,
            date_to=date_to,
            interval=interval,
        )
        resp['ta-1_1'] = predictions.get_prediction_ta_1_1_graph(
            uid=uid,
            date_from=date_from,
            date_to=date_to,
            interval=interval,
        )
        resp['ta-1_2'] = predictions.get_prediction_ta_1_2_graph(
            uid=uid,
            date_from=datetime.datetime.now(datetime.timezone.utc),
            date_to=date_to,
            interval=interval,
        )
        resp['ta-2'] = predictions.get_prediction_ta_2_graph(
            uid=uid,
            date_from=datetime.datetime.now(datetime.timezone.utc),
            date_to=date_to,
            interval=interval,
        )
    response = HttpResponse(serializer.to_json(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600 * 24 * 7)

    return response


@api_view(['GET'])
def instrument_balance(request):
    resp = None
    uid = request.GET.get('uid')

    if uid:
        resp = users.get_user_instrument_balance(instrument_uid=uid)

    response = HttpResponse(json.dumps(resp))

    patch_cache_control(response, public=True, max_age=3600)

    return response


@api_view(['GET'])
def instrument_operations(request):
    resp = None
    figi = request.GET.get('figi')

    if figi:
        resp = users.get_user_instrument_operations(instrument_figi=figi)

    response = HttpResponse(serializer.to_json(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600)

    return response


@api_view(['GET'])
def instrument_invest_calc(request):
    resp = None
    uid = request.GET.get('uid')

    if uid:
        resp = invest_calc.get_invest_calc_by_instrument_uid(instrument_uid=uid)

    response = HttpResponse(serializer.to_json(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600 * 3)

    return response


@api_view(['GET'])
def tech_analysis_graph(request):
    resp = {}
    uid = request.GET.get('uid')
    date_from = date_utils.parse_date(request.GET.get('start_date'))
    date_to = date_utils.parse_date(request.GET.get('end_date'))
    interval = IndicatorInterval(int(request.GET.get('interval')))

    if uid and date_from and date_to and interval:
        resp['RSI'] = tech_analysis.get_tech_analysis_graph(
            instrument_uid=uid,
            indicator_type=IndicatorType.INDICATOR_TYPE_RSI,
            date_from=date_from,
            date_to=date_to,
            interval=interval,
        )

        resp['BB'] = tech_analysis.get_tech_analysis_graph(
            instrument_uid=uid,
            indicator_type=IndicatorType.INDICATOR_TYPE_BB,
            date_from=date_from,
            date_to=date_to,
            interval=interval,
            deviation=Deviation(deviation_multiplier=Quotation(units=2, nano=0)),
        )

        resp['EMA'] = tech_analysis.get_tech_analysis_graph(
            instrument_uid=uid,
            indicator_type=IndicatorType.INDICATOR_TYPE_EMA,
            date_from=date_from,
            date_to=date_to,
            interval=interval,
        )

        resp['SMA'] = tech_analysis.get_tech_analysis_graph(
            instrument_uid=uid,
            indicator_type=IndicatorType.INDICATOR_TYPE_SMA,
            date_from=date_from,
            date_to=date_to,
            interval=interval,
        )

        resp['MACD'] = tech_analysis.get_tech_analysis_graph(
            instrument_uid=uid,
            indicator_type=IndicatorType.INDICATOR_TYPE_MACD,
            date_from=date_from,
            date_to=date_to,
            interval=interval,
            smoothing=Smoothing(
                fast_length=12,
                slow_length=26,
                signal_smoothing=9,
            )
        )

    response = HttpResponse(serializer.to_json(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600 * 3)

    return response


@api_view(['GET'])
def instrument_news_list_rated(request):
    resp = None
    uid = request.GET.get('uid')
    start_date = utils.parse_json_date(request.GET.get('start_date'))
    end_date = utils.parse_json_date(request.GET.get('end_date'))

    if uid and start_date and end_date:
        resp = news.get_rated_news_by_instrument_uid(
            instrument_uid=uid,
            start_date=start_date,
            end_date=end_date,
        )

    response = HttpResponse(serializer.to_json(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600 * 24 * 7)

    return response


@api_view(['GET'])
def instrument_news_rates(request):
    resp = None
    uid = request.GET.get('uid')
    start_date = utils.parse_json_date(request.GET.get('start_date'))
    end_date = utils.parse_json_date(request.GET.get('end_date'))

    if uid and start_date and end_date:
        resp = news.get_news_rate_by_instrument_uid(
            instrument_uid=uid,
            start_date=start_date,
            end_date=end_date,
        )

    response = HttpResponse(serializer.to_json(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600 * 24 * 7)

    return response


@api_view(['GET'])
def instrument_brand(request):
    resp = None
    uid = request.GET.get('uid')

    if uid:
        instrument = instruments.get_instrument_by_uid(uid=uid)

        if instrument:
            resp = instruments.get_instrument_by_ticker(ticker=instrument.ticker).brand

    response = HttpResponse(serializer.to_json(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600 * 24 * 30)

    return response


# def get_instrument_full(instrument: Instrument):
#     return {
#         'instrument': instruments.get_instrument_by_uid(uid=instrument.uid),
#         'current_price': instruments.get_instrument_price_by_date(uid=instrument.uid, date=datetime.datetime.now()),
#         'history_5_years': instruments.get_instrument_history_price_by_uid(
#             uid=instrument.uid,
#             days_count=365 * 5,
#             interval=CandleInterval.CANDLE_INTERVAL_MONTH,
#             to_date=datetime.datetime.now()
#         ),
#         'history_1_year': instruments.get_instrument_history_price_by_uid(
#             uid=instrument.uid,
#             days_count=365,
#             interval=CandleInterval.CANDLE_INTERVAL_WEEK,
#             to_date=datetime.datetime.now()
#         ),
#         'history_90_days': instruments.get_instrument_history_price_by_uid(
#             uid=instrument.uid,
#             days_count=90,
#             interval=CandleInterval.CANDLE_INTERVAL_DAY,
#             to_date=datetime.datetime.now()
#         ),
#         'forecast': getattr(getattr(
#             forecasts.get_forecasts(instrument_uid=instrument.uid),
#             'consensus',
#             {}
#         ), 'consensus', None),
#         'forecast_history': forecasts.get_db_forecasts_by_uid(uid=instrument.uid),
#         'fundamentals': fundamentals.get_fundamentals_by_asset_uid(asset_uid=instrument.asset_uid),
#         'prediction_ta1': predictions.get_prediction_ta_1_by_uid(uid=instrument.uid),
#         'prediction_ta1_graph': predictions.get_prediction_ta_1_graph_by_uid(uid=instrument.uid),
#         'balance_main': users.get_user_instrument_balance(
#             account_name='Основной',
#             instrument_uid=instrument.uid,
#         ),
#         'balance_analytics': users.get_user_instrument_balance(
#             account_name='Аналитический',
#             instrument_uid=instrument.uid,
#         ),
#         'operations_main': users.get_user_instrument_operations(
#             account_name='Основной',
#             instrument_figi=instrument.figi,
#         ),
#         'operations_analytics': users.get_user_instrument_operations(
#             account_name='Аналитический',
#             instrument_figi=instrument.figi,
#         ),
#         'news_week_0': news.get_sorted_news_by_instrument_uid(
#             instrument_uid=instrument.uid,
#             start_date=datetime.datetime.now() - datetime.timedelta(days=7),
#             end_date=datetime.datetime.now()
#         ),
#         'news_week_1': news.get_sorted_news_by_instrument_uid(
#             instrument_uid=instrument.uid,
#             start_date=datetime.datetime.now() - datetime.timedelta(days=14),
#             end_date=datetime.datetime.now() - datetime.timedelta(days=8)
#         ),
#         'brand': instruments.get_instrument_by_ticker(ticker=instrument.ticker).brand
#     }
