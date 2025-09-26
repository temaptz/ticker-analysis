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


def instruments_list(sort: int or str) -> list[Instrument]:
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

    return sorted_list


def instrument_info(uid: str, ticker: str):
    instrument = None

    if uid:
        instrument = instruments.get_instrument_by_uid(uid)

    elif ticker:
        instrument = instruments.get_instrument_by_ticker(ticker)

    if instrument:
        return serializer.get_dict_by_object_recursive(instrument)

    return None


def instrument_last_price(uid: Optional[str]):
    if not uid:
        return None
    last_price = instruments.get_instrument_last_price_by_uid(uid)
    return last_price if last_price is not None else None


def instrument_price_by_date(uid: Optional[str], date_str: Optional[str]):
    date = utils.parse_json_date(date_str)
    return instruments.get_instrument_price_by_date(uid=uid, date=date)


def instrument_history_prices(uid: Optional[str], days: Optional[str], interval: Optional[str]):
    resp = list()
    if uid and days and interval:
        for i in instruments.get_instrument_history_price_by_uid(
                uid=uid,
                days_count=int(days),
                interval=CandleInterval(int(interval)),
                to_date=date_utils.get_day_prediction_time()
        ):
            resp.append(serializer.get_dict_by_object_recursive(i))
    return resp


def instrument_forecasts(uid: Optional[str]):
    if not uid:
        return None
    f = forecasts.get_forecasts(uid)
    return f if f else None


def instrument_history_forecasts(uid: Optional[str]):
    if not uid:
        return []
    return forecasts.get_db_forecasts_history_by_uid(uid=uid)


def instrument_history_forecasts_graph(uid: Optional[str], start_date_str: Optional[str], end_date_str: Optional[str], interval_str: Optional[str]):
    resp = list()
    start_date = utils.parse_json_date(start_date_str)
    end_date = utils.parse_json_date(end_date_str)
    interval = CandleInterval(int(interval_str)) if interval_str else None
    if uid and start_date and end_date and interval:
        resp = forecasts.get_db_forecasts_graph(
            instrument_uid=uid,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
        )
    return resp


def instrument_fundamentals(uid: Optional[str]):
    resp = None
    if uid:
        instrument_obj = instruments.get_instrument_by_uid(uid)
        if instrument_obj and instrument_obj.asset_uid:
            fundamentals_resp = fundamentals.get_fundamentals_by_asset_uid(asset_uid=instrument_obj.asset_uid)
            if fundamentals_resp:
                for f in fundamentals_resp:
                    resp = serializer.get_dict_by_object_recursive(f)
    return resp


def instrument_fundamentals_history(asset_uid: Optional[str]):
    if not asset_uid:
        return []
    return fundamentals.get_db_fundamentals_history_by_uid(asset_uid=asset_uid)


def instrument_prediction_graph(uid: Optional[str], date_from_str: Optional[str], date_to_str: Optional[str], interval_str: Optional[str], models_str: Optional[str]):
    resp = {}
    date_from = date_utils.parse_date(date_from_str)
    date_to = date_utils.parse_date(date_to_str)
    interval = CandleInterval(int(interval_str)) if interval_str else None
    models = (models_str or '').split(',') if models_str is not None else []
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
    return resp


def instrument_prediction_history_graph(uid: Optional[str], date_from_str: Optional[str], date_to_str: Optional[str], interval_str: Optional[str], model_name: Optional[str]):
    resp = None
    date_from = date_utils.parse_date(date_from_str)
    date_to = date_utils.parse_date(date_to_str)
    interval = CandleInterval(int(interval_str)) if interval_str else None
    if uid and date_from and date_to and interval:
        resp = predictions.get_prediction_history_graph(
            uid=uid,
            model_name=model_name,
            date_from=date_from,
            date_to=date_to,
            interval=interval,
        )
    return resp


def instrument_prediction(uid: Optional[str], days_future: Optional[str]):
    resp = {}
    days = int(days_future) if days_future else 30
    if uid:
        date_target = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days)
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
    return resp


def instrument_prediction_consensus(uid: Optional[str], date_str: Optional[str]):
    resp = None
    date = utils.parse_json_date(date_str)
    if uid and date:
        days = (date - datetime.datetime.now(tz=datetime.timezone.utc)).days
        period_days = 3
        if days >= 21:
            period_days = 7
        if days >= 60:
            period_days = 14
        if days >= 180:
            period_days = 30
        consensus = predictions.get_prediction_cache(
            instrument_uid=uid,
            date_target=date,
            model_name=model.CONSENSUS,
            avg_days=period_days,
        )
        if consensus is not None:
            resp = utils.round_float(num=consensus, decimals=4)
    return resp


def instrument_balance(uid: Optional[str]):
    if not uid:
        return None
    return users.get_user_instrument_balance(instrument_uid=uid)


def instrument_operations(figi: Optional[str]):
    if not figi:
        return None
    return users.get_user_instrument_operations(instrument_figi=figi, account_id=users.get_analytics_account().id)


def instrument_news_list_rated(uid: Optional[str], start_date_str: Optional[str], end_date_str: Optional[str]):
    start_date = utils.parse_json_date(start_date_str)
    end_date = utils.parse_json_date(end_date_str)
    if uid and start_date and end_date:
        return news.news.get_rated_news_by_instrument_uid(
            instrument_uid=uid,
            start_date=start_date,
            end_date=end_date,
        )
    return None


def instrument_news_graph(uid: Optional[str], start_date_str: Optional[str], end_date_str: Optional[str], interval_str: Optional[str]):
    resp = None
    start_date = utils.parse_json_date(start_date_str)
    end_date = utils.parse_json_date(end_date_str)
    interval = CandleInterval(int(interval_str)) if interval_str else None
    if uid and start_date and end_date and interval:
        resp = news.news.get_rated_news_graph(
            instrument_uid=uid,
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )
    return resp


def instrument_brand(uid: Optional[str]):
    if not uid:
        return None
    instrument_obj = instruments.get_instrument_by_uid(uid=uid)
    if instrument_obj:
        return instruments.get_instrument_by_ticker(ticker=instrument_obj.ticker).brand
    return None


def instrument_invest_calc(uid: Optional[str]):
    if not uid:
        return None
    return invest_calc.get_invest_calc_by_instrument_uid(instrument_uid=uid, account_id=users.get_analytics_account().id)


def tech_analysis_graph(uid: Optional[str], start_date_str: Optional[str], end_date_str: Optional[str], interval_str: Optional[str]):
    resp = {}
    date_from = date_utils.parse_date(start_date_str)
    date_to = date_utils.parse_date(end_date_str)
    interval = IndicatorInterval(int(interval_str)) if interval_str else None
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
    return resp


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

    uid = request.GET.get('uid')
    tag_name = request.GET.get('tag_name')

    if uid and tag_name:
        if tag := db_2.instrument_tags_db.get_tag(
            instrument_uid=uid,
            tag_name=tag_name,
        ):
            if tag.tag_value is not None:
                return HttpResponse(serializer.to_json(tag.tag_value))

    return HttpResponse(None)


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
def instruments_list_endpoint(request: Request):
    return instruments_list(
        sort=request.query_params.get('sort'),
    )
    

@app.get('/instrument')
def instrument_info_endpoint(request: Request):
    return instrument_info(
        uid=request.query_params.get('uid'),
        ticker=request.query_params.get('ticker'),
    )


@app.get('/instrument/last_price')
def instrument_last_price_endpoint(request: Request):
    uid = request.query_params.get('uid')
    return instrument_last_price(uid)
    

@app.get('/instrument/price_by_date')
def instrument_price_by_date_endpoint(request: Request):
    uid = request.query_params.get('uid')
    date_str = request.query_params.get('date')
    return instrument_price_by_date(uid, date_str)
    

@app.get('/instrument/history_prices')
def instrument_history_prices_endpoint(request: Request):
    uid = request.query_params.get('uid')
    days = request.query_params.get('days')
    interval = request.query_params.get('interval')
    return instrument_history_prices(uid, days, interval)
    

@app.get('/instrument/forecasts')
def instrument_forecasts_endpoint(request: Request):
    uid = request.query_params.get('uid')
    return instrument_forecasts(uid)
    

@app.get('/instrument/history_forecasts')
def instrument_history_forecasts_endpoint(request: Request):
    uid = request.query_params.get('uid')
    return instrument_history_forecasts(uid)
    

@app.get('/instrument/history_forecasts_graph')
def instrument_history_forecasts_graph_endpoint(request: Request):
    uid = request.query_params.get('uid')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    interval = request.query_params.get('interval')
    return instrument_history_forecasts_graph(uid, start_date, end_date, interval)
    

@app.get('/instrument/fundamentals')
def instrument_fundamentals_endpoint(request: Request):
    uid = request.query_params.get('uid')
    return instrument_fundamentals(uid)
    

@app.get('/instrument/fundamentals_history')
def instrument_fundamentals_history_endpoint(request: Request):
    asset_uid = request.query_params.get('asset_uid')
    return instrument_fundamentals_history(asset_uid)
    

@app.get('/instrument/prediction_graph')
def instrument_prediction_graph_endpoint(request: Request):
    uid = request.query_params.get('uid')
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    interval = request.query_params.get('interval')
    models = request.query_params.get('models')
    return instrument_prediction_graph(uid, date_from, date_to, interval, models)
    

@app.get('/instrument/prediction_history_graph')
def instrument_prediction_history_graph_endpoint(request: Request):
    uid = request.query_params.get('uid')
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    interval = request.query_params.get('interval')
    model_name = request.query_params.get('model_name')
    return instrument_prediction_history_graph(uid, date_from, date_to, interval, model_name)
    

@app.get('/instrument/prediction')
def instrument_prediction_endpoint(request: Request):
    uid = request.query_params.get('uid')
    days_future = request.query_params.get('days_future')
    return instrument_prediction(uid, days_future)
    

@app.get('/instrument/prediction_consensus')
def instrument_prediction_consensus_endpoint(request: Request):
    uid = request.query_params.get('uid')
    date = request.query_params.get('date')
    return instrument_prediction_consensus(uid, date)
    

@app.get('/instrument/balance')
def instrument_balance_endpoint(request: Request):
    uid = request.query_params.get('uid')
    return instrument_balance(uid)
    

@app.get('/instrument/operations')
def instrument_operations_endpoint(request: Request):
    figi = request.query_params.get('figi')
    return instrument_operations(figi)
    

@app.get('/instrument/news_list_rated')
def instrument_news_list_rated_endpoint(request: Request):
    uid = request.query_params.get('uid')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    return instrument_news_list_rated(uid, start_date, end_date)
    

@app.get('/instrument/news_graph')
def instrument_news_graph_endpoint(request: Request):
    uid = request.query_params.get('uid')
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    interval = request.query_params.get('interval')
    return instrument_news_graph(uid, date_from, date_to, interval)
    

@app.get('/instrument/brand')
def instrument_brand_endpoint(request: Request):
    uid = request.query_params.get('uid')
    return instrument_brand(uid)
    

@app.get('/instrument/invest_calc')
def instrument_invest_calc_endpoint(request: Request):
    uid = request.query_params.get('uid')
    return instrument_invest_calc(uid)
    

@app.get('/instrument/tech_analysis_graph')
def tech_analysis_graph_endpoint(request: Request):
    uid = request.query_params.get('uid')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    interval = request.query_params.get('interval')
    return tech_analysis_graph(uid, start_date, end_date, interval)
    

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

