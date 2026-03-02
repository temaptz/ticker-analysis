import numpy as np
from enum import IntEnum
from t_tech.invest import Instrument, CandleInterval
from t_tech.invest.schemas import IndicatorType
from datetime import datetime, timedelta, timezone

from lib import utils, instruments, date_utils, tech_analysis, learn, graph_printing

TARGET_MIN_DAYS_COUNT = 1
TARGET_MAX_DAYS_COUNT = 20
CANDLES_COUNT = 20

class TargetResult(IntEnum):
    upper = 1
    lower = -1
    same = 0

def get_feature_names() -> list:
    feature_names = []

    for i in range(CANDLES_COUNT):
        feature_names.extend([
            f'volume_norm_{i}',
            f'rsi_norm_{i}',
        ])

    return feature_names


MODEL_NAME = learn.model.TA_3_tech


class Ta3VolumeAnalysisCard:
    is_ok: bool = True
    is_fill_empty: bool = False
    instrument: Instrument | None = None
    date: datetime | None = None
    price: float | None = None

    target_result: TargetResult | None = None

    candles: list = []

    def __init__(
            self,
            instrument: Instrument | None = None,
            date: datetime | None = None,
            is_fill_empty=False,
    ):
        self.instrument = instrument
        self.date = date
        self.is_fill_empty = is_fill_empty

        if not self.instrument or not self.date:
            self.is_ok = False
            return

        try:
            self.fill_card()
            self.check_x()
        except Exception as e:
            print('ERROR INIT Ta3LearningCard', e)
            self.is_ok = False

    def fill_card(self):
        self.price = instruments.get_instrument_price_by_date(uid=self.instrument.uid, date=self.date)
        self.target_result = self._get_target_result()
        self.candles = self.get_candles()

    def get_candles(self) -> list:
        result = []
        date_from = self.date.replace(hour=21, minute=0, second=0) - timedelta(days=(CANDLES_COUNT + 10))
        date_to = self.date.replace(hour=20, minute=59, second=59) - timedelta(days=1)

        price_candles = instruments.get_instrument_history_price_by_uid(
            uid=self.instrument.uid,
            days_count=(CANDLES_COUNT + 10),
            interval=CandleInterval.CANDLE_INTERVAL_DAY,
            to_date=date_to,
        )

        if not price_candles or len(price_candles) < CANDLES_COUNT:
            return []

        price_candles = sorted(price_candles, key=lambda x: x.time)
        last_candles = price_candles[-CANDLES_COUNT:]
        rsi_items = tech_analysis.get_tech_analysis(
            instrument_uid=self.instrument.uid,
            indicator_type=IndicatorType.INDICATOR_TYPE_RSI,
            date_from=date_from,
            date_to=date_to,
            interval=tech_analysis.IndicatorInterval.INDICATOR_INTERVAL_ONE_DAY,
            length=14
        )
        rsi_dict = {date_utils.parse_date(i.timestamp): utils.get_price_by_quotation(i.signal) for i in rsi_items}

        volumes = [float(candle.volume) if candle.volume else 0 for candle in price_candles]
        
        ma_fast = tech_analysis.ema(volumes, 12)
        ma_slow = tech_analysis.ema(volumes, 26)
        
        pvo_values = []
        for i in range(len(ma_fast)):
            if ma_slow[i] is not None and ma_fast[i] is not None and ma_slow[i] != 0:
                pvo = (ma_fast[i] - ma_slow[i]) / ma_slow[i]
            else:
                pvo = 0
            pvo_values.append(pvo)
        
        sign_values = tech_analysis.ema(pvo_values, 9)
        volume_hist_values = [pvo_values[i] - sign_values[i] for i in range(len(pvo_values))]
        volume_hist_last = volume_hist_values[-CANDLES_COUNT:]

        dates = []
        for i, candle in enumerate(last_candles):
            candle_date = date_utils.parse_date(candle.time)
            dates.append(candle_date)
            result.append({
                'volume_norm': volume_hist_last[i],
                'rsi_norm': rsi_dict.get(candle_date) / 100,
            })

        # volume_norm_data = [c['volume_norm'] for c in result]
        # rsi_norm_data = [c['rsi_norm'] for c in result]
        #
        # print("\n" + "="*120)
        # print("VOLUME NORM (PVO Histogram * 10)")
        # print("="*120)
        # graph_printing.print_graph(y_data=volume_norm_data, date_from=dates[0], date_to=dates[-1])
        #
        # print("="*120)
        # print("RSI NORM (RSI / 100)")
        # print("="*120)
        # graph_printing.print_graph(y_data=rsi_norm_data, date_from=dates[0], date_to=dates[-1])

        return result

    def _get_target_result(self) -> TargetResult | None:
        target_from = self.date + timedelta(days=1)
        target_to = target_from + timedelta(days=10)

        if target_to < datetime.now(timezone.utc):
            if ema_graph := tech_analysis.get_tech_analysis(
                instrument_uid=self.instrument.uid,
                indicator_type=IndicatorType.INDICATOR_TYPE_EMA,
                date_from=target_from,
                date_to=target_to,
                interval=tech_analysis.IndicatorInterval.INDICATOR_INTERVAL_ONE_DAY,
            ):
                ema_sorted = sorted(ema_graph, key=lambda x: x.timestamp)
                ema_newest = utils.get_price_by_quotation(ema_sorted[-1].signal)

                if ema_newest is not None:
                    if ema_newest < -0.01:
                        return TargetResult.lower
                    elif ema_newest > 0.01:
                        return TargetResult.upper
                    else:
                        return TargetResult.same

        return None

    def check_x(self):
        x_values = self.get_x()
        feature_names = get_feature_names()

        def is_invalid(x):
            if x is None:
                return True
            if isinstance(x, (int, float, np.floating)):
                return not np.isfinite(x)
            return False

        invalid_fields = []
        for name, value in zip(feature_names, x_values):
            if is_invalid(value):
                invalid_fields.append(name)
        
        if invalid_fields:
            print(f'{MODEL_NAME} CARD HAS {len(invalid_fields)} INVALID VALUES (None/NaN/Inf)', self.instrument.ticker, self.date)
            print(f'Invalid fields: {invalid_fields}')
            if not self.is_fill_empty:
                self.is_ok = False
                return

    def get_x(self) -> list[float]:
        x: list[float] = []

        for i in range(CANDLES_COUNT):
            candle = self.candles[i] if i < len(self.candles) else {}
            x.extend([
                learn.learn_utils.to_numpy_float(candle.get('volume_norm')),
                learn.learn_utils.to_numpy_float(candle.get('rsi_norm')),
            ])

        return x

    def get_y(self) -> float or None:
        return self.target_result

    def get_csv_record(self) -> dict:
        result = {}
        x = self.get_x()
        y = self.get_y()
        fields_x = get_feature_names()

        for i, name in enumerate(fields_x):
            result[name] = x[i]

        result['result'] = y

        return result
