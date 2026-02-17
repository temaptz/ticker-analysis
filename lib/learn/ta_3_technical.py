import numpy as np
from t_tech.invest import Instrument, CandleInterval
from t_tech.invest.schemas import IndicatorType
from datetime import datetime, timedelta, timezone

from lib import utils, instruments, news, date_utils, tech_analysis, learn

TARGET_MIN_DAYS_COUNT = 1
TARGET_MAX_DAYS_COUNT = 20
CANDLES_COUNT = 20

def get_feature_names() -> list:
    feature_names = [
        'target_date_days',
        'currency',
        'country_of_risk',
    ]

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


class Ta3TechnicalAnalysisCard:
    is_ok: bool = True
    is_fill_empty: bool = False
    instrument: Instrument | None = None
    date: datetime | None = None
    target_date: datetime | None = None
    target_date_days: int | None = None
    price: float | None = None
    target_price: float | None = None

    candles: list = []

    def __init__(
            self,
            instrument: Instrument | None = None,
            date: datetime | None = None,
            target_date: datetime | None = None,
            is_fill_empty=False,
    ):
        self.instrument = instrument
        self.date = date
        self.target_date = target_date
        self.is_fill_empty = is_fill_empty

        if not self.instrument or not self.date or not self.target_date:
            self.is_ok = False
            return

        if date > target_date:
            self.is_ok = False
            return

        days_diff = (target_date - date).days
        if days_diff < TARGET_MIN_DAYS_COUNT or days_diff > TARGET_MAX_DAYS_COUNT:
            self.is_ok = False
            return

        try:
            self.target_date_days = days_diff
            self.fill_card()
            self.check_x()
        except Exception as e:
            print('ERROR INIT Ta3LearningCard', e)
            self.is_ok = False

    def fill_card(self):
        self.price = instruments.get_instrument_price_by_date(uid=self.instrument.uid, date=self.date)
        self.target_price = instruments.get_instrument_price_by_date(uid=self.instrument.uid, date=self.target_date) if (self.target_date < datetime.now(timezone.utc)) else None
        self.candles = self.get_candles(days_count=CANDLES_COUNT)

    def get_candles(self, days_count: int) -> list:
        result = []
        date_from = self.date - timedelta(days=80)
        date_to = (self.date - timedelta(days=1)).replace(hour=20, minute=59, second=59)

        price_candles = instruments.get_instrument_history_price_by_uid(
            uid=self.instrument.uid,
            days_count=days_count + 50,
            interval=CandleInterval.CANDLE_INTERVAL_DAY,
            to_date=date_to,
        )

        if not price_candles:
            return []

        price_candles = sorted(price_candles, key=lambda x: x.time)
        price_candles = [c for c in price_candles if getattr(c, 'is_complete', True)]
        last_candles = price_candles[-(days_count + 1):]

        ema50_items = tech_analysis.get_tech_analysis(
            instrument_uid=self.instrument.uid,
            indicator_type=IndicatorType.INDICATOR_TYPE_EMA,
            date_from=date_from,
            date_to=date_to,
            interval=tech_analysis.IndicatorInterval.INDICATOR_INTERVAL_ONE_DAY,
        )

        rsi_items = tech_analysis.get_tech_analysis(
            instrument_uid=self.instrument.uid,
            indicator_type=IndicatorType.INDICATOR_TYPE_RSI,
            date_from=date_from,
            date_to=date_to,
            interval=tech_analysis.IndicatorInterval.INDICATOR_INTERVAL_ONE_DAY,
        )

        macd_items = tech_analysis.get_tech_analysis(
            instrument_uid=self.instrument.uid,
            indicator_type=IndicatorType.INDICATOR_TYPE_MACD,
            date_from=date_from,
            date_to=date_to,
            interval=tech_analysis.IndicatorInterval.INDICATOR_INTERVAL_ONE_DAY,
        )

        ema50_dict = {date_utils.parse_date(i.timestamp): utils.get_price_by_quotation(i.signal) for i in ema50_items}
        rsi_dict = {date_utils.parse_date(i.timestamp): utils.get_price_by_quotation(i.signal) for i in rsi_items}
        macd_hist_dict = {date_utils.parse_date(i.timestamp): (utils.get_price_by_quotation(i.macd) - utils.get_price_by_quotation(i.signal)) for i in macd_items}
        prev_close_abs = None

        volume_avg = sum(i.volume for i in last_candles) / len(last_candles)

        for candle in last_candles:
            if prev_close_abs is None:
                prev_close_abs = utils.get_price_by_quotation(candle.close)
                continue

            close_abs = utils.get_price_by_quotation(candle.close)
            news_score = news.news.get_influence_score(
                instrument_uid=self.instrument.uid,
                start_date=(candle.time - timedelta(days=3)),
                end_date=candle.time,
            )

            result.append({
                'candle_close_rel': utils.get_change_relative(
                    current_value=prev_close_abs,
                    next_value=close_abs,
                ),
                'candle_open_rel': utils.get_change_relative(
                    current_value=close_abs,
                    next_value=utils.get_price_by_quotation(candle.open),
                ),
                'candle_low_rel': utils.get_change_relative(
                    current_value=close_abs,
                    next_value=utils.get_price_by_quotation(candle.low),
                ),
                'candle_high_rel': utils.get_change_relative(
                    current_value=close_abs,
                    next_value=utils.get_price_by_quotation(candle.high),
                ),
                'candle_ema50_rel': utils.get_change_relative(
                    current_value=close_abs,
                    next_value=ema50_dict.get(candle.time),
                ),
                'candle_volume_rel': utils.get_change_relative(
                    current_value=volume_avg,
                    next_value=candle.volume,
                ),
                'candle_rsi': rsi_dict.get(candle.time) / 100,
                'candle_macd_rel': macd_hist_dict.get(candle.time) / close_abs,
                'candle_macd_sign': np.sign(macd_hist_dict.get(candle.time)),
                'candle_news_influence_score': ((news_score / 10) if news_score else None),
            })

            prev_close_abs = close_abs

        return result

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
