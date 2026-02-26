import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Union

from lib import utils, instruments, fundamentals, forecasts, learn, tech_analysis, date_utils, agent
from t_tech.invest import StatisticResponse
from t_tech.invest.schemas import IndicatorType, IndicatorInterval

MODEL_NAME = learn.model.TA_3_fundamental
MIN_DAYS = 90 # Минимальное количество дней до прогнозного периода
MAX_DAYS = 370 # Максимальное количество дней до прогнозного периода
REPORT_DURATION_DAYS = 90 # Это период за который собирается отчетность
REPORTS_COUNT = 3 # Количество отчетов

FUNDAMENTAL_FIELDS = [
    'market_capitalization', # Рыночная капитализация
    'high_price_last_52_weeks', # Максимум за год
    'low_price_last_52_weeks', # Минимум за год
    'average_daily_volume_last_10_days', # Средний объем торгов за 10 дней
    'average_daily_volume_last_4_weeks', # Средний объем торгов за месяц
    'beta', # Нормализованная волатильность
    'shares_outstanding', # Количество акций в обращении
    'price_to_book_ttm', # Соотношение рыночной капитализации компании к ее балансовой стоимости
    'total_enterprise_value_mrq', # Рыночная стоимость компании
    'total_debt_to_equity_mrq', # Соотношение долга к собственному капиталу
    'total_debt_to_ebitda_mrq', # Total Debt/EBITDA
    'ebitda_ttm', # EBITDA
    'revenue_ttm',
    'total_debt_mrq',
    'eps_ttm',
    'pe_ratio_ttm',
    'ev_to_ebitda_mrq',
    'dividend_payout_ratio_fy',
]

def get_feature_names() -> List[str]:
    return FUNDAMENTAL_FIELDS


class Ta3FundamentalAnalysisCard:
    is_ok: bool = True
    instrument: Optional[instruments.Instrument] = None
    date: Optional[datetime] = None
    price: Optional[float] = None
    forecast_price_change: Optional[float] = None
    target_profit_percent: Optional[float] = None
    fundamentals: Optional[StatisticResponse] = None

    fundamentals_history: List[Dict[str, Any]] = []

    def __init__(
            self,
            instrument: instruments.Instrument,
            date: datetime,
            is_fill_empty: bool = False,
    ):
        self.instrument = instrument
        self.date = date

        if not self.instrument or not self.date:
            self.is_ok = False
            return

        if date > datetime.now(timezone.utc):
            self.is_ok = False
            return

        try:
            self.fill_card()
            self.check_x()
        except Exception as e:
            print('ERROR INIT Ta3FundamentalAnalysisCard', e)
            self.is_ok = False

    def fill_card(self):
        if not self.instrument or not self.date:
            self.is_ok = False
            return

        self.price = instruments.get_instrument_price_by_date(uid=self.instrument.uid, date=self.date)
        self.target_profit_percent = self._get_target_profit_percent()

        if f := fundamentals.get_db_fundamentals_by_asset_uid_date_2(
                asset_uid=self.instrument.asset_uid,
                date=(self.date - timedelta(days=(REPORT_DURATION_DAYS + 30)))
        ):
            self.fundamentals = f

    def _get_forecast_price_change(self, is_fill_empty: bool = False) -> Optional[float]:
        try:
            if (forecast_data := forecasts.get_db_forecast_by_uid_date(
                uid=self.instrument.uid,
                date=self.date
            )) and forecast_data[1] and forecast_data[1].consensus.consensus:
                if target_price := utils.get_price_by_quotation(forecast_data[1].consensus.consensus):
                    return utils.get_change_relative(
                        current_value=self.price,
                        next_value=target_price,
                    )
        except Exception as e:
            print(f'ERROR get_forecast_price_change: {e}')

        return 0 if is_fill_empty else None

    def _get_target_profit_percent(self) -> float or None:
        if (tech := tech_analysis.get_tech_analysis(
            instrument_uid=self.instrument.uid,
            indicator_type=IndicatorType.INDICATOR_TYPE_SMA,
            date_from=(self.date + timedelta(days=MIN_DAYS)),
            date_to=(self.date + timedelta(days=MAX_DAYS)),
            interval=IndicatorInterval.INDICATOR_INTERVAL_ONE_DAY,
            length=30,
        )) and len(tech):
            if max_sma_profit := max([utils.get_price_by_quotation(i.signal) for i in tech]):
                return utils.get_change_relative(
                    current_value=self.price,
                    next_value=max_sma_profit,
                )

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
            learn.learn_utils.to_numpy_float(self.fundamentals.market_capitalization),
            learn.learn_utils.to_numpy_float(self.fundamentals.high_price_last_52_weeks),
            learn.learn_utils.to_numpy_float(self.fundamentals.low_price_last_52_weeks),
            learn.learn_utils.to_numpy_float(self.fundamentals.average_daily_volume_last_10_days),
            learn.learn_utils.to_numpy_float(self.fundamentals.average_daily_volume_last_4_weeks),
            learn.learn_utils.to_numpy_float(self.fundamentals.beta),
            learn.learn_utils.to_numpy_float(self.fundamentals.shares_outstanding),
            learn.learn_utils.to_numpy_float(self.fundamentals.price_to_book_ttm),
            learn.learn_utils.to_numpy_float(self.fundamentals.total_enterprise_value_mrq),
            learn.learn_utils.to_numpy_float(self.fundamentals.total_debt_to_equity_mrq),
            learn.learn_utils.to_numpy_float(self.fundamentals.total_debt_to_ebitda_mrq),
            learn.learn_utils.to_numpy_float(self.fundamentals.ebitda_ttm),
            learn.learn_utils.to_numpy_float(self.fundamentals.revenue_ttm),
            learn.learn_utils.to_numpy_float(self.fundamentals.total_debt_mrq),
            learn.learn_utils.to_numpy_float(self.fundamentals.eps_ttm),
            learn.learn_utils.to_numpy_float(self.fundamentals.pe_ratio_ttm),
            learn.learn_utils.to_numpy_float(self.fundamentals.ev_to_ebitda_mrq),
            learn.learn_utils.to_numpy_float(self.fundamentals.dividend_payout_ratio_fy),
        ]

    def get_y(self) -> Optional[float]:
        return self.target_profit_percent or None

    def get_csv_record(self) -> Dict[str, Any]:
        result = {}
        x = self.get_x()
        y = self.get_y()
        fields_x = get_feature_names()

        for i, name in enumerate(fields_x):
            result[name] = x[i]

        result['result'] = y

        return result