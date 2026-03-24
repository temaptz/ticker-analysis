from enum import Enum

class PriceDirection(Enum):
    PRICE_DOWN = 'lower'
    PRICE_SAME = 'same'
    PRICE_UP = 'upper'