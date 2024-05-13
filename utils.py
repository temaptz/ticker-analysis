from tinkoff.invest.schemas import Quotation


def get_price_by_quotation(price: Quotation) -> float:
    return float(str(price.units)+'.'+str(price.nano))