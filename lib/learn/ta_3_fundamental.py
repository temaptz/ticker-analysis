import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Union

from lib import utils, instruments, fundamentals, forecasts, learn, tech_analysis, date_utils, agent
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
]

def get_feature_names() -> List[str]:
    feature_names = [
        'currency',
        'country_of_risk',

        'forecast_price_change',
    ]

    for i in range(REPORTS_COUNT):
        feature_names.extend([f'{field_name}_{i}' for field_name in FUNDAMENTAL_FIELDS])

    return feature_names


class Ta3FundamentalAnalysisCard:
    is_ok: bool = True
    instrument: Optional[instruments.Instrument] = None
    date: Optional[datetime] = None
    price: Optional[float] = None
    forecast_price_change: Optional[float] = None
    target_profit_percent: Optional[float] = None

    fundamentals_history: List[Dict[str, Any]] = []

    def __init__(
            self,
            instrument: instruments.Instrument,
            date: datetime,
            fill_empty: bool = False
    ):
        self.instrument = instrument
        self.date = date

        if not self.instrument or not self.date:
            self.is_ok = False
            return

        if date + timedelta(days=250) > datetime.now(timezone.utc): # Надо MAX_DAYS пока так потерпим
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
        self.fundamentals_history = self._get_fundamentals_history()

    def _get_fundamentals_history(self) -> List[Dict[str, Any]]:
        result = []

        if prev_fundamentals := fundamentals.get_db_fundamentals_by_asset_uid_date_2(
                asset_uid=self.instrument.asset_uid,
                date=(self.date - timedelta(days=(REPORT_DURATION_DAYS + 30)))
        ):
            for date in date_utils.get_dates_interval_list(
                date_from=(self.date - timedelta(days=REPORT_DURATION_DAYS)),
                date_to=self.date,
                interval_seconds=((REPORT_DURATION_DAYS / (REPORTS_COUNT - 1)) * 3600 * 24),
                is_order_descending=False,
            ):
                if current_fundamentals := fundamentals.get_db_fundamentals_by_asset_uid_date_2(
                    asset_uid=self.instrument.asset_uid,
                    date=date
                ):
                    result.append({
                        field: utils.get_change_relative(
                            current_value=getattr(prev_fundamentals, field, None),
                            next_value=getattr(current_fundamentals, field, None),
                        ) for field in FUNDAMENTAL_FIELDS
                    })

                    prev_fundamentals = current_fundamentals

        return result

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

        if len(self.fundamentals_history) < 5:
            print(f'{MODEL_NAME} CARD IS NOT OK BY FUNDAMENTALS HISTORY', self.instrument.ticker if self.instrument else 'None', self.date)
            print(f'Received {len(self.fundamentals_history)} quarters, need 5')
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
        x: list[float] = [
            self.instrument.currency,
            self.instrument.country_of_risk,
            self.forecast_price_change,
        ]

        for i in self.fundamentals_history:
            x.extend([learn.learn_utils.to_numpy_float(i.get(field, None)) for field in FUNDAMENTAL_FIELDS])

        return x

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