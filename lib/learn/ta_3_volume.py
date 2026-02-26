import numpy as np
from enum import IntEnum
from t_tech.invest import Instrument, CandleInterval
from t_tech.invest.schemas import IndicatorType
from datetime import datetime, timedelta, timezone

from lib import utils, instruments, news, date_utils, tech_analysis, learn

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
            f'candle_open_rel_{i}',
            f'candle_close_rel_{i}',
            f'candle_high_rel_{i}',
            f'candle_low_rel_{i}',
            f'candle_ema50_rel_{i}',
            f'candle_volume_rel_{i}',
            f'candle_rsi_{i}',
            f'candle_macd_rel_{i}',
            f'candle_macd_sign_{i}',
            f'candle_news_influence_score_{i}',
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

        for candle in last_candles:
            result.append({
                'volume': 0,
                'rsi': rsi_dict.get(date_utils.parse_date(candle.time)),
            })

        return result

    def _get_target_result(self) -> TargetResult | None:
        target_from = self.date + timedelta(days=1)
        target_to = target_from + timedelta(days=10)

        if target_to < datetime.now(timezone.utc):
            if sma_graph := tech_analysis.get_tech_analysis(
                instrument_uid=self.instrument.uid,
                indicator_type=IndicatorType.INDICATOR_TYPE_SMA,
                date_from=target_from,
                date_to=target_to,
                interval=tech_analysis.IndicatorInterval.INDICATOR_INTERVAL_ONE_DAY,
            ):
                sma_values = [utils.get_price_by_quotation(i.signal) for i in sma_graph]
                if (sma_max := max(sma_values)) or sma_max == 0:
                    sma_max_change = utils.get_change_relative(
                        current_value=self.price,
                        next_value=sma_max,
                    )
                    if sma_max_change is not None:
                        if sma_max_change < -0.01:
                            return TargetResult.lower
                        elif sma_max_change > 0.01:
                            return TargetResult.upper
                        else:
                            return TargetResult.same
        return None

    def check_x(self):
        if self.price is None:
            print(f'{MODEL_NAME} CARD IS NOT OK BY CURRENT PRICE', self.instrument.ticker, self.date)
            self.is_ok = False
            return

        if len(self.candles) != CANDLES_COUNT:
            print(f'{MODEL_NAME} CARD IS NOT OK BY DAILY CANDLES', self.instrument.ticker, self.date)
            self.is_ok = False
            return

        news_scores = [candle.get('candle_news_influence_score') for candle in self.candles]
        if all(score is None for score in news_scores):
            print(f'{MODEL_NAME} CARD IS NOT OK: ALL news_influence_score VALUES ARE None', self.instrument.ticker, self.date)
            if not self.is_fill_empty:
                self.is_ok = False
                return

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
            if 'news_influence_score' in name:
                continue
            if is_invalid(value):
                invalid_fields.append(name)
        
        if invalid_fields:
            print(f'{MODEL_NAME} CARD HAS {len(invalid_fields)} INVALID VALUES (None/NaN/Inf)', self.instrument.ticker, self.date)
            print(f'Invalid fields: {invalid_fields}')
            if not self.is_fill_empty:
                self.is_ok = False
                return

    def get_x(self) -> list[float]:
        x: list[float] = [
            self.target_date_days,
            self.instrument.currency,
            self.instrument.country_of_risk,
        ]

        for i in range(CANDLES_COUNT):
            candle = self.candles[i] if i < len(self.candles) else {}
            x.extend([
                learn.learn_utils.to_numpy_float(candle.get('candle_open_rel')),
                learn.learn_utils.to_numpy_float(candle.get('candle_close_rel')),
                learn.learn_utils.to_numpy_float(candle.get('candle_high_rel')),
                learn.learn_utils.to_numpy_float(candle.get('candle_low_rel')),
                learn.learn_utils.to_numpy_float(candle.get('candle_ema50_rel')),
                learn.learn_utils.to_numpy_float(candle.get('candle_volume_rel')),
                learn.learn_utils.to_numpy_float(candle.get('candle_rsi')),
                learn.learn_utils.to_numpy_float(candle.get('candle_macd_rel')),
                learn.learn_utils.to_numpy_float(candle.get('candle_macd_sign')),
                learn.learn_utils.to_numpy_float(candle.get('candle_news_influence_score') or 0),
            ])

        return x

    def get_y(self) -> float or None:
        if self.price and self.target_price:
            return utils.get_change_relative(current_value=self.price, next_value=self.target_price)
        return None

    def get_csv_record(self) -> dict:
        result = {}
        x = self.get_x()
        y = self.get_y()
        fields_x = get_feature_names()

        for i, name in enumerate(fields_x):
            result[name] = x[i]

        result['result'] = y

        return result
