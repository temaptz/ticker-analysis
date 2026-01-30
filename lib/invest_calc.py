import datetime
from t_tech.invest import Operation, OperationType, Instrument, OperationState
from lib import utils, instruments, users, logger, predictions

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

    def get_average_price(self) -> float:
        # 1) Берём только исполненные BUY/SELL и сортируем по возрастанию даты
        ops = [
            o for o in self.operations
            if o.state == OperationState.OPERATION_STATE_EXECUTED
               and o.operation_type in (OperationType.OPERATION_TYPE_BUY, OperationType.OPERATION_TYPE_SELL)
        ]
        ops.sort(key=lambda o: o.date)  # важно: по возрастанию!

        # 2) FIFO-учёт открытых лотов
        open_positions = []  # элементы: {'quantity': int, 'cost_per_share': float}

        for o in ops:
            if o.operation_type == OperationType.OPERATION_TYPE_BUY:
                qty = int(o.quantity or 0)
                if qty <= 0:
                    continue

                # Предпочитаем цену за 1 шт из o.price; если вдруг её нет — fallback на payment/qty
                if getattr(o, 'price', None):
                    cost_per_share = float(utils.get_price_by_quotation(price=o.price))
                else:
                    total_payment = abs(float(utils.get_price_by_quotation(price=o.payment)))
                    cost_per_share = total_payment / qty if qty else 0.0

                open_positions.append({'quantity': qty, 'cost_per_share': cost_per_share})

            elif o.operation_type == OperationType.OPERATION_TYPE_SELL:
                remain = int(o.quantity or 0)
                # Снимаем из начала списка (FIFO)
                while remain > 0 and open_positions:
                    first = open_positions[0]
                    if first['quantity'] <= remain:
                        remain -= first['quantity']
                        open_positions.pop(0)
                    else:
                        first['quantity'] -= remain
                        remain = 0
                # Если remain > 0 и лотов нет — игнорируем 'излишнюю' продажу для avg (ничего не осталось списывать)

        # 3) Средняя по оставшимся лотам
        total_qty = sum(p['quantity'] for p in open_positions)
        if total_qty == 0:
            return 0.0

        total_cost = sum(p['quantity'] * p['cost_per_share'] for p in open_positions)
        return total_cost / total_qty

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
def get_invest_calc_by_instrument_uid(instrument_uid: str, account_id: int = None) -> dict or None:
    result = {
        'balance': None,
        'current_price': None,
        'market_value': None,
        'potential_profit': None,
        'potential_profit_percent': None,
        'avg_price': None,
        'operations': None,
    }

    instrument = instruments.get_instrument_by_uid(uid=instrument_uid)
    current_price = instruments.get_instrument_last_price_by_uid(uid=instrument_uid)

    if instrument and current_price:
        balance_qty = users.get_user_instrument_balance(instrument_uid=instrument_uid, account_id=account_id)

        if balance_qty:
            operations = users.get_user_instrument_operations(instrument_figi=instrument.figi, account_id=account_id)

            if operations and len(operations) > 0:
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

    return None


def is_recommend_to_buy(instrument_uid: str) -> bool:
    last_price = instruments.get_instrument_last_price_by_uid(uid=instrument_uid)
    prediction_consensus = predictions.get_predictions_consensus(
        instrument_uid=instrument_uid,
        date_target=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)
    )

    if last_price and prediction_consensus and prediction_consensus > last_price:
        change_percent = ((prediction_consensus - last_price) / last_price) * 100
        return change_percent > 10

    return False


def is_recommend_to_sell(instrument_uid: str) -> bool:
    calc = get_invest_calc_by_instrument_uid(instrument_uid=instrument_uid)

    if calc and calc['balance'] is not None and calc['potential_profit_percent'] is not None and calc['balance'] > 0 and calc['potential_profit_percent'] > 10:
        return True

    return False


def get_report() -> None:
    to_buy: [Instrument] = []
    to_sell: [Instrument] = []
    for i in instruments.get_instruments_white_list():
        print(i.ticker)

        if is_recommend_to_buy(i.uid):
            to_buy.append(i)
        if is_recommend_to_sell(i.uid):
            to_sell.append(i)

    for i in to_buy:
        print('TO BUY', i.ticker, i.name)

    for i in to_sell:
        print('TO SELL', i.ticker, i.name)
