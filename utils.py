from tinkoff.invest.schemas import (
    Quotation,
    HistoricCandle,
)


def get_price_by_candle(candle: HistoricCandle) -> float:
    return (get_price_by_quotation(price=candle.high) + get_price_by_quotation(price=candle.low)) / 2


def get_price_by_quotation(price: Quotation) -> float:
    return float(str(price.units)+'.'+str(price.nano))
