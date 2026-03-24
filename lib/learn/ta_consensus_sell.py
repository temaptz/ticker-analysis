import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from lib import utils, instruments, learn, tech_analysis, agent
from t_tech.invest.schemas import IndicatorType, IndicatorInterval

MODEL_NAME = learn.model.TA_consensus_sell
TARGET_DAYS_FROM = 10 # Минимальное количество дней до прогнозного периода
TARGET_DAYS_TO = 10 + 60 # Максимальное количество дней до прогнозного периода

def get_feature_names() -> List[str]:
    return [
        'volume',
        'macd',
        'rsi',
        'tech',
        'news',
        'fundamental',
        'profit',
    ]


class TaConsensusSellCard:
    is_ok: bool = True
    instrument: Optional[instruments.Instrument] = None
    account_id: Optional[str] = None
    date: Optional[datetime] = None
    price: Optional[float] = None
    macd_rated: Optional[dict] = None
    rsi_rated: Optional[dict] = None
    tech_rated: Optional[dict] = None
    news_rated: Optional[dict] = None
    fundamental_rated: Optional[dict] = None
    volume_rated: Optional[dict] = None
    profit_rated: Optional[dict] = None
    result: Optional[float] = None

    def __init__(
            self,
            instrument: instruments.Instrument,
            account_id: str,
            date: datetime,
            is_fill_empty: bool = False,
    ):
        self.instrument = instrument
        self.account_id = account_id
        self.date = date

        if not self.instrument or not self.account_id or not self.date:
            self.is_ok = False
            return

        if date > datetime.now(timezone.utc):
            self.is_ok = False
            return

        try:
            self.fill_card()
            self.check_x()
        except Exception as e:
            print('ERROR INIT TaConsensusSellCard', e)
            self.is_ok = False

    def fill_card(self):
        self.price = instruments.get_instrument_price_by_date(uid=self.instrument.uid, date=self.date)
        self.macd_rated = agent.macd.macd_sell_rate(instrument_uid=self.instrument.uid, date=self.date)
        self.rsi_rated = agent.rsi.rsi_sell_rate(instrument_uid=self.instrument.uid, date=self.date)
        self.tech_rated = agent.tech.get_tech_sell_rate(instrument_uid=self.instrument.uid, date=self.date)
        self.news_rated = agent.news.get_news_sell_rate(instrument_uid=self.instrument.uid, date=self.date)
        self.fundamental_rated = agent.fundamental.get_fundamental_sell_rate(instrument_uid=self.instrument.uid, date=self.date)
        self.volume_rated = agent.volume.get_volume_sell_rate(instrument_uid=self.instrument.uid, date=self.date)
        self.profit_rated = agent.profit.get_profit_sell_rate(instrument_uid=self.instrument.uid, account_id=self.account_id)

        if self.date < datetime.now(tz=timezone.utc):
            self.result = self._get_result()

    def _get_result(self) -> float or None:
        if (tech := tech_analysis.get_tech_analysis(
            instrument_uid=self.instrument.uid,
            indicator_type=IndicatorType.INDICATOR_TYPE_SMA,
            date_from=(self.date + timedelta(days=TARGET_DAYS_FROM)),
            date_to=(self.date + timedelta(days=TARGET_DAYS_TO)),
            interval=IndicatorInterval.INDICATOR_INTERVAL_ONE_DAY,
            length=9,
        )) and len(tech):
            if max_sma_profit := max([utils.get_price_by_quotation(i.signal) for i in tech]):
                if (max_price_change := utils.get_change_relative(
                    current_value=self.price,
                    next_value=max_sma_profit,
                )) or max_price_change == 0:
                    if max_price_change < 0:
                        return 1
                    if max_price_change > 0.1:
                        return 0

                    return agent.utils.linear_interpolation(max_price_change, 0, 0.1, 1, 0)

        return None


    def check_x(self):
        if self.price is None:
            print(f'{MODEL_NAME} CARD IS NOT OK BY CURRENT PRICE', self.instrument.ticker if self.instrument else 'None', self.date)
            self.is_ok = False
            return

        x_values = self.get_x()
        feature_names = get_feature_names()

        def is_invalid(x: Any) -> bool:
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
            print(f'{MODEL_NAME} CARD HAS {len(invalid_fields)} INVALID VALUES', self.instrument.ticker if self.instrument else 'None', self.date)
            print(f'Invalid fields: {invalid_fields}')
            self.is_ok = False
            return

    def get_x(self) -> list[float]:
        return [
            learn.learn_utils.to_numpy_float(self.volume_rated.get('rate', None)),
            learn.learn_utils.to_numpy_float(self.macd_rated.get('rate', None)),
            learn.learn_utils.to_numpy_float(self.rsi_rated.get('rate', None)),
            learn.learn_utils.to_numpy_float(self.tech_rated.get('rate', None)),
            learn.learn_utils.to_numpy_float(self.news_rated.get('rate', None)),
            learn.learn_utils.to_numpy_float(self.fundamental_rated.get('rate', None)),
            learn.learn_utils.to_numpy_float(self.profit_rated.get('rate', None)),
        ]

    def get_y(self) -> Optional[str]:
        return self.result if self.result else None

    def get_csv_record(self) -> Dict[str, Any]:
        result = {}
        x = self.get_x()
        y = self.get_y()
        fields_x = get_feature_names()

        for i, name in enumerate(fields_x):
            result[name] = x[i]

        result['result'] = y

        return result