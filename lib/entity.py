class MarketData:
    market_capitalization: float
    high_price_last_52_weeks: float
    low_price_last_52_weeks: float
    average_daily_volume_last_10_days: float
    average_daily_volume_last_4_weeks: float
    revenue_ttm: float
    ebitda_ttm: float
    net_income_ttm: float
    free_cash_flow_ttm: float
    total_enterprise_value_mrq: float
    net_margin_mrq: float
    total_debt_mrq: float
    current_ratio_mrq: float
    one_year_annual_revenue_growth_rate: float

    def __init__(self, **kwargs):
        self.market_capitalization = kwargs['market_capitalization']
        self.high_price_last_52_weeks = kwargs['high_price_last_52_weeks']
        self.low_price_last_52_weeks = kwargs['low_price_last_52_weeks']
        self.average_daily_volume_last_10_days = kwargs['average_daily_volume_last_10_days']
        self.average_daily_volume_last_4_weeks = kwargs['average_daily_volume_last_4_weeks']
        self.revenue_ttm = kwargs['revenue_ttm']
        self.ebitda_ttm = kwargs['ebitda_ttm']
        self.net_income_ttm = kwargs['net_income_ttm']
        self.free_cash_flow_ttm = kwargs['free_cash_flow_ttm']
        self.total_enterprise_value_mrq = kwargs['total_enterprise_value_mrq']
        self.net_margin_mrq = kwargs['net_margin_mrq']
        self.total_debt_mrq = kwargs['total_debt_mrq']
        self.current_ratio_mrq = kwargs['current_ratio_mrq']
        self.one_year_annual_revenue_growth_rate = kwargs['one_year_annual_revenue_growth_rate']


class EntityResolved(MarketData):
    date: str
    price1: float
    price2: float
    price3: float
    price4: float
    price5: float
    prediction: float
    result: float

    def __init__(self, **kwargs):
        self.date = kwargs['date']
        self.price0 = kwargs['price0']
        self.price1 = kwargs['price1']
        self.price2 = kwargs['price2']
        self.price3 = kwargs['price3']
        self.price4 = kwargs['price4']
        self.price5 = kwargs['price5']
        self.prediction = kwargs['prediction']
        self.result = kwargs['result']
        super(EntityResolved, self).__init__(**kwargs)

    def display(self):
        print('****************************')
        print('PRICE 5   :', self.price5)
        print('PRICE 4   :', self.price4)
        print('PRICE 3   :', self.price3)
        print('PRICE 2   :', self.price2)
        print('PRICE 1   :', self.price1)
        print('PRICE 0   :', self.price0)
        print('DATE      :', self.date)
        print('PREDICTION:', self.prediction)
        print('RESULT    :', self.result)
        print('EBIDTA    :', self.ebitda_ttm)
        print('INCOME    :', self.net_income_ttm)
        print('MARKET    :', self.market_capitalization)
        print('****************************')
