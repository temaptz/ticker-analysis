from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import Any, Optional
import json

# ==== original imports from views, adjusted ====
import datetime
from tinkoff.invest import CandleInterval, Instrument, Quotation
from tinkoff.invest.schemas import IndicatorType, IndicatorInterval, Deviation, Smoothing

# Ported from views.py expected dependencies
from lib import serializer, instruments, forecasts, predictions, news, utils, fundamentals, date_utils, invest_calc, tech_analysis, db_2, users
from lib.learn import ta_1_2, ta_2, ta_2_1, model
import json

# ==== Django shims ====
class _HttpResponse:
    def __init__(self, content: Any = "", status: int = 200, content_type: str = "application/json"):
        self.content = content
        self.status_code = status
        self.content_type = content_type
        self.headers = {}

def HttpResponse(content: Any = "", status: int = 200, content_type: str = "application/json"):
    return _HttpResponse(content=content, status=status, content_type=content_type)

def patch_cache_control(response: _HttpResponse, public: bool = False, max_age: Optional[int] = None):
    directives = []
    directives.append("public" if public else "private")
    if max_age is not None:
        try:
            directives.append(f"max-age={int(max_age)}")
        except Exception:
            pass
    response.headers["Cache-Control"] = ", ".join(directives)

class _ShimRequest:
    def __init__(self, fastapi_request: Request, json_body: Optional[dict] = None):
        self._fa_req = fastapi_request
        self.GET = fastapi_request.query_params
        self.data = json_body or {}
        self.method = fastapi_request.method

# ==== app ====
app = FastAPI(title="API")

@app.get("/health")
def health():
    return {"status": "ok"}

# ==== original view functions ported verbatim, expecting Django-like request ====


def instruments_list(request):
    sort = request.GET.get('sort')

    sorted_list = instruments.get_instruments_white_list()

    if sort and (sort == 1 or sort == '1'):
        sorted_list = users.sort_instruments_for_buy(
            instruments_list=sorted_list
        )
    elif sort and (sort == 2 or sort == '2'):
        sorted_list = users.sort_instruments_for_sell(
            instruments_list=sorted_list
        )
    elif sort and (sort == 3 or sort == '3'):
        sorted_list = users.sort_instruments_last_operation(
            instruments_list=sorted_list
        )
    elif sort and (sort == 4 or sort == '4'):
        sorted_list = users.sort_instruments_cost(
            instruments_list=sorted_list
        )

    response = HttpResponse(serializer.to_json(sorted_list))

    if len(sorted_list) > 0:
        patch_cache_control(response, public=True, max_age=3600)

    return response


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
        resp = serializer.get_dict_by_object_recursive(instrument)

    response = HttpResponse(json.dumps(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600 * 24 * 7)

    return response


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


def instrument_price_by_date(request):
    uid = request.GET.get('uid')
    date = utils.parse_json_date(request.GET.get('date'))

    data = instruments.get_instrument_price_by_date(uid=uid, date=date)
    response = HttpResponse(data or json.dumps(None))

    if data:
        patch_cache_control(response, public=True, max_age=3600 * 24)

    return response


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
                to_date=date_utils.get_day_prediction_time()
        ):
            resp.append(serializer.get_dict_by_object_recursive(i))

    response = HttpResponse(json.dumps(resp))

    if resp and len(resp):
        patch_cache_control(response, public=True, max_age=3600 * 3)

    return response


def instrument_forecasts(request):
    resp = None

    if uid := request.GET.get('uid'):
        if f := forecasts.get_forecasts(uid):
            resp = f

    response = HttpResponse(serializer.to_json(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600 * 24 * 7)

    return response


def instrument_history_forecasts(request):
    resp = list()
    uid = request.GET.get('uid')

    if uid:
        resp = forecasts.get_db_forecasts_history_by_uid(uid=uid)

    response = HttpResponse(serializer.to_json(resp))

    if len(resp) > 0:
        patch_cache_control(response, public=True, max_age=3600 * 24 * 7)

    return response


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


def instrument_fundamentals(request):
    resp = None
    uid = request.GET.get('uid')

    if uid:
        if instrument := instruments.get_instrument_by_uid(uid):
            if instrument.asset_uid:
                fundamentals_resp = fundamentals.get_fundamentals_by_asset_uid(asset_uid=instrument.asset_uid)

                if fundamentals_resp:
                    for f in fundamentals_resp:
                        resp = serializer.get_dict_by_object_recursive(f)

    response = HttpResponse(json.dumps(resp))

    if resp and len(resp):
        patch_cache_control(response, public=True, max_age=3600 * 24 * 7)

    return response


def instrument_fundamentals_history(request):
    resp = list()
    asset_uid = request.GET.get('asset_uid')

    if asset_uid:
        resp = fundamentals.get_db_fundamentals_history_by_uid(asset_uid=asset_uid)

    response = HttpResponse(serializer.to_json(resp))

    if resp and len(resp):
        patch_cache_control(response, public=True, max_age=3600 * 24 * 7)

    return response


def instrument_prediction_graph(request):
    resp = {}
    uid = request.GET.get('uid')
    date_from = date_utils.parse_date(request.GET.get('date_from'))
    date_to = date_utils.parse_date(request.GET.get('date_to'))
    interval = CandleInterval(int(request.GET.get('interval')))
    models = (request.GET.get('models') or '').split(',') or []

    if uid and date_from and date_to and interval:
        model_names = models if len(models) else [
            model.TA_1,
            model.TA_1_1,
            model.TA_1_2,
            model.TA_2,
            model.TA_2_1,
            model.CONSENSUS
        ]

        for model_name in model_names:
            resp[model_name] = predictions.get_prediction_graph(
                uid=uid,
                model_name=model_name,
                date_from=datetime.datetime.now(datetime.timezone.utc),
                date_to=date_to,
                interval=interval,
            )
    response = HttpResponse(serializer.to_json(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600 * 24)

    return response


def instrument_prediction_history_graph(request):
    resp = None
    uid = request.GET.get('uid')
    date_from = date_utils.parse_date(request.GET.get('date_from'))
    date_to = date_utils.parse_date(request.GET.get('date_to'))
    interval = CandleInterval(int(request.GET.get('interval')))
    model_name = request.GET.get('model_name')

    if uid and date_from and date_to and interval:
        resp = predictions.get_prediction_history_graph(
            uid=uid,
            model_name=model_name,
            date_from=date_from,
            date_to=date_to,
            interval=interval,
        )

    response = HttpResponse(serializer.to_json(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600 * 24)

    return response


def instrument_prediction(request):
    resp = {}
    uid = request.GET.get('uid')
    days_future = int(request.GET.get('days_future')) if request.GET.get('days_future') else 30

    if uid:
        date_target = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days_future)
        current_price = instruments.get_instrument_last_price_by_uid(uid=uid)

        resp['relative'] = {}
        resp['relative'][model.TA_1] = predictions.get_prediction_cache(instrument_uid=uid, date_target=date_target, model_name=model.TA_1)
        resp['relative'][model.TA_1_1] = predictions.get_prediction_cache(instrument_uid=uid, date_target=date_target, model_name=model.TA_1_1)
        resp['relative'][model.TA_1_2] = predictions.get_prediction_cache(instrument_uid=uid, date_target=date_target, model_name=model.TA_1_2)
        resp['relative'][model.TA_2] = predictions.get_prediction_cache(instrument_uid=uid, date_target=date_target, model_name=model.TA_2)
        resp['relative'][model.TA_2_1] = predictions.get_prediction_cache(instrument_uid=uid, date_target=date_target, model_name=model.TA_2_1)
        resp['relative'][model.CONSENSUS] = predictions.get_prediction_cache(instrument_uid=uid, date_target=date_target, model_name=model.CONSENSUS)


        resp[model.TA_1] = utils.get_price_by_change_relative(current_price=current_price, relative_change=resp['relative'][model.TA_1])
        resp[model.TA_1_1] = utils.get_price_by_change_relative(current_price=current_price, relative_change=resp['relative'][model.TA_1_1])
        resp[model.TA_1_2] = utils.get_price_by_change_relative(current_price=current_price, relative_change=resp['relative'][model.TA_1_2])
        resp[model.TA_2] = utils.get_price_by_change_relative(current_price=current_price, relative_change=resp['relative'][model.TA_2])
        resp[model.TA_2_1] = utils.get_price_by_change_relative(current_price=current_price, relative_change=resp['relative'][model.TA_2_1])
        resp[model.CONSENSUS] = utils.get_price_by_change_relative(current_price=current_price, relative_change=resp['relative'][model.CONSENSUS])

    response = HttpResponse(json.dumps(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600)

    return response


def instrument_prediction_consensus(request):
    resp = None
    uid = request.GET.get('uid')
    date = utils.parse_json_date(request.GET.get('date'))

    if uid and date:
        days = (date - datetime.datetime.now(tz=datetime.timezone.utc)).days
        period_days = 3

        if days >= 21:
            period_days = 7
        if days >= 60:
            period_days = 14
        if days >= 180:
            period_days = 30

        if consensus := predictions.get_prediction_cache(
                instrument_uid=uid,
                date_target=date,
                model_name=model.CONSENSUS,
                avg_days=period_days,
        ):
            resp = utils.round_float(num=consensus, decimals=4)

    response = HttpResponse(json.dumps(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600)

    return response


def instrument_balance(request):
    resp = None
    uid = request.GET.get('uid')

    if uid:
        resp = users.get_user_instrument_balance(instrument_uid=uid)

    response = HttpResponse(json.dumps(resp))

    patch_cache_control(response, public=True, max_age=3600)

    return response


def instrument_operations(request):
    resp = None
    figi = request.GET.get('figi')

    if figi:
        resp = users.get_user_instrument_operations(instrument_figi=figi, account_id=users.get_analytics_account().id)

    response = HttpResponse(serializer.to_json(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600)

    return response


def instrument_news_list_rated(request):
    resp = None
    uid = request.GET.get('uid')
    start_date = utils.parse_json_date(request.GET.get('start_date'))
    end_date = utils.parse_json_date(request.GET.get('end_date'))

    if uid and start_date and end_date:
        resp = news.news.get_rated_news_by_instrument_uid(
            instrument_uid=uid,
            start_date=start_date,
            end_date=end_date,
        )

    response = HttpResponse(serializer.to_json(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600 * 24 * 7)

    return response


def instrument_news_graph(request):
    resp = None
    uid = request.GET.get('uid')
    start_date = utils.parse_json_date(request.GET.get('date_from'))
    end_date = utils.parse_json_date(request.GET.get('date_to'))
    interval = CandleInterval(int(request.GET.get('interval')))

    if uid and start_date and end_date and interval:
        resp = news.news.get_rated_news_graph(
            instrument_uid=uid,
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )

    response = HttpResponse(serializer.to_json(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600 * 24 * 7)

    return response


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


def instrument_invest_calc(request):
    resp = None
    uid = request.GET.get('uid')

    if uid:
        resp = invest_calc.get_invest_calc_by_instrument_uid(instrument_uid=uid, account_id=users.get_analytics_account().id)

    response = HttpResponse(serializer.to_json(resp))

    if resp:
        patch_cache_control(response, public=True, max_age=3600 * 3)

    return response


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


def instrument_tag(request):
    if request.method == 'POST':
        uid = request.data.get('uid') or request.GET.get('uid')
        tag_name = request.data.get('tag_name') or request.GET.get('tag_name')
        tag_value = request.data.get('tag_value') or request.GET.get('tag_value')

        if uid and tag_name and tag_value is not None:
            db_2.instrument_tags_db.upset_tag(
                        instrument_uid=uid,
                        tag_name='llm_sell_conclusion',
                        tag_value=tag_value,
                    )

            return HttpResponse(serializer.to_json({'ok': True}))

        return HttpResponse(
            serializer.to_json({'ok': False, 'error': 'uid, tag_name, tag_value are required'}),
            status=400,
        )

    response = None
    uid = request.GET.get('uid')
    tag_name = request.GET.get('tag_name')

    if uid and tag_name:
        if tag := db_2.instrument_tags_db.get_tag(
            instrument_uid=uid,
            tag_name=tag_name,
        ):
            if tag.tag_value:
                response = HttpResponse(serializer.to_json(tag.tag_value))

    if response:
        patch_cache_control(response, public=True, max_age=60)

    return response


# ==== adapter ====
def _to_fastapi_response(result, response: Response):
    # If original view returned our shim response
    if isinstance(result, _HttpResponse):
        # propagate headers
        for k, v in result.headers.items():
            response.headers[k] = v
        return Response(content=result.content, status_code=result.status_code, media_type=result.content_type)
    # If it returned a dict or list, send JSON
    if isinstance(result, (dict, list)):
        return JSONResponse(content=result)
    # If returned text
    if isinstance(result, str):
        return PlainTextResponse(content=result)
    # None -> 404
    if result is None:
        raise HTTPException(status_code=404, detail="Not found")
    # Fallback
    try:
        return JSONResponse(content=json.loads(result))
    except Exception:
        return PlainTextResponse(content=str(result))


@app.get('/instruments')
async def instruments_list_endpoint(request: Request, response: Response):
    print('INSTRUMENTS LIST', request)
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = instruments_list(shim)
    return _to_fastapi_response(result, response)
    

@app.get('/instrument')
async def instrument_info_endpoint(request: Request, response: Response):
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = instrument_info(shim)
    return _to_fastapi_response(result, response)
    

@app.get('/instrument/last_price')
async def instrument_last_price_endpoint(request: Request, response: Response):
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = instrument_last_price(shim)
    return _to_fastapi_response(result, response)
    

@app.get('/instrument/price_by_date')
async def instrument_price_by_date_endpoint(request: Request, response: Response):
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = instrument_price_by_date(shim)
    return _to_fastapi_response(result, response)
    

@app.get('/instrument/history_prices')
async def instrument_history_prices_endpoint(request: Request, response: Response):
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = instrument_history_prices(shim)
    return _to_fastapi_response(result, response)
    

@app.get('/instrument/forecasts')
async def instrument_forecasts_endpoint(request: Request, response: Response):
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = instrument_forecasts(shim)
    return _to_fastapi_response(result, response)
    

@app.get('/instrument/history_forecasts')
async def instrument_history_forecasts_endpoint(request: Request, response: Response):
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = instrument_history_forecasts(shim)
    return _to_fastapi_response(result, response)
    

@app.get('/instrument/history_forecasts_graph')
async def instrument_history_forecasts_graph_endpoint(request: Request, response: Response):
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = instrument_history_forecasts_graph(shim)
    return _to_fastapi_response(result, response)
    

@app.get('/instrument/fundamentals')
async def instrument_fundamentals_endpoint(request: Request, response: Response):
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = instrument_fundamentals(shim)
    return _to_fastapi_response(result, response)
    

@app.get('/instrument/fundamentals_history')
async def instrument_fundamentals_history_endpoint(request: Request, response: Response):
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = instrument_fundamentals_history(shim)
    return _to_fastapi_response(result, response)
    

@app.get('/instrument/prediction_graph')
async def instrument_prediction_graph_endpoint(request: Request, response: Response):
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = instrument_prediction_graph(shim)
    return _to_fastapi_response(result, response)
    

@app.get('/instrument/prediction_history_graph')
async def instrument_prediction_history_graph_endpoint(request: Request, response: Response):
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = instrument_prediction_history_graph(shim)
    return _to_fastapi_response(result, response)
    

@app.get('/instrument/prediction')
async def instrument_prediction_endpoint(request: Request, response: Response):
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = instrument_prediction(shim)
    return _to_fastapi_response(result, response)
    

@app.get('/instrument/prediction_consensus')
async def instrument_prediction_consensus_endpoint(request: Request, response: Response):
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = instrument_prediction_consensus(shim)
    return _to_fastapi_response(result, response)
    

@app.get('/instrument/balance')
async def instrument_balance_endpoint(request: Request, response: Response):
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = instrument_balance(shim)
    return _to_fastapi_response(result, response)
    

@app.get('/instrument/operations')
async def instrument_operations_endpoint(request: Request, response: Response):
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = instrument_operations(shim)
    return _to_fastapi_response(result, response)
    

@app.get('/instrument/news_list_rated')
async def instrument_news_list_rated_endpoint(request: Request, response: Response):
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = instrument_news_list_rated(shim)
    return _to_fastapi_response(result, response)
    

@app.get('/instrument/news_graph')
async def instrument_news_graph_endpoint(request: Request, response: Response):
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = instrument_news_graph(shim)
    return _to_fastapi_response(result, response)
    

@app.get('/instrument/brand')
async def instrument_brand_endpoint(request: Request, response: Response):
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = instrument_brand(shim)
    return _to_fastapi_response(result, response)
    

@app.get('/instrument/invest_calc')
async def instrument_invest_calc_endpoint(request: Request, response: Response):
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = instrument_invest_calc(shim)
    return _to_fastapi_response(result, response)
    

@app.get('/instrument/tech_analysis_graph')
async def tech_analysis_graph_endpoint(request: Request, response: Response):
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = tech_analysis_graph(shim)
    return _to_fastapi_response(result, response)
    

@app.get('/instrument/tag')
async def instrument_tag_endpoint(request: Request, response: Response):
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = instrument_tag(shim)
    return _to_fastapi_response(result, response)
    

@app.post('/instrument/tag')
async def instrument_tag_endpoint(request: Request, response: Response):
    shim = _ShimRequest(request, json_body=(await request.json() if request.method in ('POST','PUT','PATCH') else None))
    result = instrument_tag(shim)
    return _to_fastapi_response(result, response)

