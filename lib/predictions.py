import datetime
from lib.learn import ta_2_1, model
from lib import date_utils, logger, utils, instruments, predictions_cache, learn
from lib.db_2 import predictions_db
from t_tech.invest import CandleInterval


def get_prediction(
        instrument_uid: str,
        date_target: datetime.datetime,
        model_name: model = model.CONSENSUS,
        date_current: datetime.datetime = None,
        avg_days: int = 1,
        is_ignore_cache: bool = False,
) -> float or None:
    try:
        days = [date_target + datetime.timedelta(days=o) for o in ([0] + [d for k in range(1, avg_days) for d in (-k, k)])][:avg_days]
        day_results: list[float] = []

        for day in days:
            day_target = date_utils.get_day_prediction_time(day)
            predict_day = None

            if is_ignore_cache is False and date_current is None and ((cached := get_prediction_cache(
                    instrument_uid=instrument_uid,
                    model_name=model_name,
                    date_target=date_target,
                    avg_days=1,
            )) is not None):
                predict_day = cached
            elif model_name == model.TA_2_1:
                predict_day = ta_2_1.predict_future_relative_change(
                    instrument_uid=instrument_uid,
                    date_target=day_target,
                    date_current=date_current,
                    is_fill_empty=True,
                )
            elif model_name == model.TA_3_tech:
                p = learn.ta_3_technical_learn.predict_future(
                    instrument_uid=instrument_uid,
                    date_target=day_target,
                    date_current=date_current,
                    is_fill_empty=True,
                )
                if p is not None and -2 < p < 2:
                    predict_day = p
            elif model_name == model.CONSENSUS:
                predict_day = get_relative_predictions_consensus(
                    instrument_uid=instrument_uid,
                    date_target=day_target,
                )

            if predict_day:
                if -3 < predict_day < 3:
                    day_results.append(predict_day)

        if len(day_results) > 0:
            return sum(day_results) / len(day_results)

    except Exception as e:
        logger.log_error(method_name='get_prediction', error=e)

    return None


def get_prediction_cache(
        instrument_uid: str,
        date_target: datetime.datetime,
        model_name: model = model.CONSENSUS,
        avg_days: int = 1,
) -> float or None:
    try:
        days = [date_target + datetime.timedelta(days=o) for o in ([0] + [d for k in range(1, avg_days) for d in (-k, k)])][:avg_days]
        day_results: list[float] = []

        for day in days:
            if (cached := predictions_cache.get_prediction_cache(
                instrument_uid=instrument_uid,
                model_name=model_name,
                date_target=date_utils.get_day_prediction_time(day),
            )) is not None:
                if -3 < cached < 3:
                    day_results.append(cached)


        if len(day_results) > 0:
            return sum(day_results) / len(day_results)

    except Exception as e:
        logger.log_error(method_name='get_prediction_cache', error=e)

    return None


def get_prediction_graph(uid: str, model_name: model, date_from: datetime.datetime, date_to: datetime.datetime, interval: CandleInterval) -> list:
    try:
        result = list()
        current_price = instruments.get_instrument_last_price_by_uid(uid=uid)

        if current_price is not None:
            date_from_utc = date_utils.get_day_prediction_time(date_from)
            date_to_utc = date_utils.get_day_prediction_time(date_to)

            for date in date_utils.get_dates_interval_list(
                    date_from=date_from_utc,
                    date_to=date_to_utc,
                    interval_seconds=date_utils.get_interval_sec_by_candle(interval)
            ):
                if model_name == model.CONSENSUS:
                    prediction_item = get_relative_predictions_consensus(instrument_uid=uid, date_target=date)
                else:
                    prediction_item = get_prediction_cache(
                        instrument_uid=uid,
                        date_target=date,
                        model_name=model_name,
                    )

                if prediction_item is not None:
                    if prediction_price := utils.get_value_by_change_relative(
                            current_value=current_price,
                            relative_change=prediction_item,
                    ):
                        result.append({
                            'prediction': utils.round_float(num=prediction_price, decimals=4),
                            'prediction_percent': utils.round_float(num=(prediction_item * 100), decimals=2),
                            'date': date,
                        })

            return result
    except Exception as e:
        print('ERROR get_prediction_graph_by_uid', e)

    return []


@logger.error_logger
def get_prediction_history_graph(
        uid: str,
        model_name: str,
        date_from: datetime.datetime,
        date_to: datetime.datetime,
        interval: CandleInterval,
) -> dict:
    result = {}
    current_price = instruments.get_instrument_last_price_by_uid(uid)

    for prediction in predictions_db.get_predictions_by_uid_date(
        uid=uid,
        date_from=date_from,
        date_to=date_to,
        model_name=model_name,
    ):
        dt = date_utils.parse_date(prediction.date)
        target_dt = date_utils.parse_date(prediction.target_date)

        if model_name in [model.TA_1, model.TA_1_1]:
            key_date = date_to
        else:
            key_date = dt

        key = key_date.isoformat()

        if key not in result:
            result[key] = []

        if not any(p['date'] == target_dt for p in result[key]):
            if (
                    model_name == learn.model.TA_1
                    or model_name == learn.model.TA_1_1
                    or (model_name == learn.model.TA_1_2 and key_date < datetime.datetime(year=2025, month=9, day=15))
                    or (model_name == learn.model.TA_2 and key_date < datetime.datetime(year=2025, month=8, day=18))
                    or (model_name == learn.model.TA_2_1 and key_date < datetime.datetime(year=2025, month=8, day=18))
            ):
                p_abs = prediction.prediction
                p_percent = utils.get_change_relative(
                    current_value=current_price,
                    next_value=p_abs,
                )
            else:
                p_abs = utils.get_value_by_change_relative(
                    current_value=current_price,
                    relative_change=prediction.prediction,
                )
                p_percent = prediction.prediction


            result[key].append({
                'prediction': p_abs,
                'prediction_percent': p_percent,
                'date': target_dt,
                'model_name': model_name,
            })

    # Sort each list of predictions by date
    return {k: sorted(
        rebuild_points_by_interval(
            points=v,
            date_from=date_from,
            date_to=date_to,
            interval=interval,
        ),
        key=lambda x: x['date']
    ) for k, v in sorted(result.items())}


def get_relative_predictions_consensus(instrument_uid: str, date_target: datetime.datetime) -> float or None:
    weights = {
        model.TA_2_1: 1,
        model.TA_3_tech: 10,
    }

    prediction_ta_2_1 = get_prediction_cache(
        instrument_uid=instrument_uid,
        date_target=date_target,
        model_name=model.TA_2_1,
    )
    prediction_ta_3_tech = get_prediction_cache(
        instrument_uid=instrument_uid,
        date_target=date_target,
        model_name=model.TA_3_tech,
    )

    total_sum = 0
    total_weight = 0

    if prediction_ta_2_1 is not None:
        total_sum += (prediction_ta_2_1 * weights[model.TA_2_1])
        total_weight += weights[model.TA_2_1]

    if prediction_ta_3_tech is not None:
        total_sum += (prediction_ta_3_tech * weights[model.TA_3_tech])
        total_weight += weights[model.TA_3_tech]

    if total_weight > 0:
        return total_sum / total_weight

    return None


def rebuild_points_by_interval(
        points: list[dict],
        date_from: datetime.datetime,
        date_to: datetime.datetime,
        interval: CandleInterval,
) -> list[dict]:
    """
    Группировка точек по интервалам [start, end) с усреднением.
    Пропуск интервалов без данных.
    """
    try:
        if not points or date_from >= date_to:
            return []

        # normalize bounds
        df_utc = date_utils.convert_to_utc(date_from)
        dt_utc = date_utils.convert_to_utc(date_to)

        interval_sec = date_utils.get_interval_sec_by_candle(interval)

        # buckets в UTC-aware
        buckets: list[tuple[datetime.datetime, datetime.datetime]] = []
        for start in date_utils.get_dates_interval_list(
                date_from=df_utc,
                date_to=dt_utc,
                interval_seconds=interval_sec,
        ):
            s = date_utils.convert_to_utc(start)
            buckets.append((s, s + datetime.timedelta(seconds=interval_sec)))

        # normalize point dates to UTC-aware и упорядочим
        pts = []
        for p in points:
            d = date_utils.convert_to_utc(p['date'])
            np = dict(p)
            np['date'] = d
            pts.append(np)
        pts.sort(key=lambda x: x['date'])

        n = len(pts)
        i = 0
        out: list[dict] = []

        for start, end in buckets:
            while i < n and pts[i]['date'] < start:
                i += 1

            j = i
            vs, vs_pct = [], []

            while j < n and pts[j]['date'] < end:
                p = pts[j]
                if (v := p.get('prediction')) is not None:
                    vs.append(v)
                if (vp := p.get('prediction_percent')) is not None:
                    vs_pct.append(vp)
                j += 1

            if vs or vs_pct:
                # model_name оставим от последней точки интервала (если нужна единообразность — возьмите первый)
                mdl = pts[j - 1].get('model_name') if j > i else None
                out.append({
                    'prediction': (sum(vs) / len(vs)) if vs else None,
                    'prediction_percent': (sum(vs_pct) / len(vs_pct)) if vs_pct else None,
                    'date': start,           # UTC-aware граница интервала
                    'model_name': mdl,
                })

            i = j

        return out
    except Exception as e:
        print('ERROR aggregate_points_by_interval', e)
        return []
