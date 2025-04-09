from tinkoff.invest import Operation, OperationType
from lib import utils, instruments, users, logger

class InvestCalc:

    operations_list: list[Operation] = []
    current_price: float = None
    balance_qty: int = None

    def __init__(
            self,
            operations: list[Operation],
            current_price: float,
            balance_qty: int,
    ):
        self.operations = operations
        self.current_price = current_price
        self.balance_qty = balance_qty

        try:
            self.fill_card()
            self.check_self()
        except Exception as e:
            print('ERROR INIT TA-1_2 LearningCard', e)
            self.is_ok = False

    def get_average_price(self) -> float:
        # Храним "открытые лоты"
        open_positions = []  # каждый элемент: {'quantity': int, 'cost_per_share': float}

        for o in self.operations:
            if o.operation_type == OperationType.OPERATION_TYPE_BUY:
                open_positions.append({
                    'quantity': o.quantity,
                    'cost_per_share': utils.get_price_by_quotation(price=o.price) or 0
                })
            elif o.operation_type == OperationType.OPERATION_TYPE_SELL:
                remain_to_sell = o.quantity

                while remain_to_sell > 0 and open_positions:
                    first_pos = open_positions[0]

                    if first_pos['quantity'] <= remain_to_sell:
                        remain_to_sell -= first_pos['quantity']
                        open_positions.pop(0)
                    else:
                        first_pos['quantity'] -= remain_to_sell
                        remain_to_sell = 0

        total_qty = sum(pos['quantity'] for pos in open_positions)
        total_cost = sum(pos['quantity'] * pos['cost_per_share'] for pos in open_positions)

        return total_cost / total_qty if total_qty > 0 else 0

    def get_market_value(self) -> float:
        return self.balance_qty * self.current_price

    def get_profit(self) -> float:
        avg_price = self.get_average_price()
        cost_basis = avg_price * self.balance_qty
        market_value = self.current_price * self.balance_qty
        return market_value - cost_basis

    def get_profit_percentage(self) -> float:
        profit = self.get_profit()
        avg_price = self.get_average_price()
        cost_basis = avg_price * self.balance_qty
        return (profit / cost_basis) * 100 if cost_basis != 0 else 0


@logger.error_logger
def get_invest_calc_by_instrument_uid(instrument_uid: str):
    result = {
        'balance': None,
        'current_price': None,
        'market_value': None,
        'potential_profit': None,
        'potential_profit_percent': None,
        'avg_price': None,
        'operations': None,
    }

    current_price = None
    instrument = instruments.get_instrument_by_uid(uid=instrument_uid)
    last_prices = instruments.get_instrument_last_price_by_uid(uid=instrument_uid)

    if last_prices and last_prices[0]:
        current_price = utils.get_price_by_quotation(last_prices[0].price)

    if instrument and current_price:
        balance_qty = users.get_user_instrument_balance(instrument_uid=instrument_uid)

        if balance_qty:
            operations = users.get_user_instrument_operations(instrument_figi=instrument.figi)

            if operations and len(operations):
                calc = InvestCalc(
                    operations=operations,
                    current_price=current_price,
                    balance_qty=balance_qty,
                )

                result['balance'] = balance_qty
                result['current_price'] = current_price
                result['market_value'] = calc.get_market_value()
                result['potential_profit'] = calc.get_profit()
                result['potential_profit_percent'] = calc.get_profit_percentage()
                result['avg_price'] = calc.get_average_price()
                result['operations'] = operations

    return result


def get_report() -> None:
    print('REPORT')
