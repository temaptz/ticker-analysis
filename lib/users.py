import math
import datetime
import pytz
from t_tech.invest import (
    Client,
    constants,
    GetAccountsResponse,
    PositionsResponse,
    Operation,
    OperationState,
    OperationType,
    Instrument,
    Account, PostOrderResponse, OrderType, OrderDirection, OrderState,
)
from const import TINKOFF_INVEST_TOKEN
from lib import cache, instruments, utils, logger, invest_calc, predictions, db_2, agent, serializer


@cache.ttl_cache(ttl=3600)
def get_user_instrument_balance(instrument_uid: str, account_id: str = None) -> int:
    result = 0

    try:
        for account in get_accounts():
            if account_id is None or account.id == account_id:
                positions = get_positions(account_id=account.id)
                for instrument in positions.securities:
                    if instrument and instrument.instrument_uid == instrument_uid:
                        result += instrument.balance + instrument.blocked

    except Exception as e:
        logger.log_error(method_name='get_user_instrument_balance', error=e)

    return result


def get_user_money_rub(account_id: str) -> float:
    result = 0.0

    try:
        if account_id and (positions := get_positions(account_id=account_id)):
                if positions.money and len(positions.money) > 0:
                    for m in positions.money:
                        if m.currency == 'rub':
                            result += utils.get_price_by_quotation(m)
                if positions.blocked:
                    for b in positions.blocked:
                        if b.currency == 'rub':
                            result -= utils.get_price_by_quotation(b)

    except Exception as e:
        logger.log_error(method_name='get_user_money_rub', error=e)

    return result


def post_buy_order(instrument_uid: str, quantity_lots: int, price_rub: float, account_id: str) -> PostOrderResponse or None:
    try:
        with Client(TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            price_increment = utils.get_price_by_quotation(
                price=instruments.get_instrument_by_uid(uid=instrument_uid).min_price_increment
            )
            price = utils.get_quotation_by_price(math.floor(price_rub / price_increment) * price_increment)

            if order := client.orders.post_order(
                instrument_id=instrument_uid,
                quantity=quantity_lots,
                price=price,
                account_id=account_id,
                order_type=OrderType.ORDER_TYPE_LIMIT,
                direction=OrderDirection.ORDER_DIRECTION_BUY,
            ):
                return order

    except Exception as e:
        logger.log_error(
            method_name='post_buy_order',
            error=e,
            debug_info=serializer.to_json({
                'instrument_name': instruments.get_instrument_by_uid(instrument_uid).name,
                'quantity_lots': quantity_lots,
                'price_rub': price_rub,
                'price_increment': price_increment,
                'price_quotation': price,
            }),
        )

    return None


def post_sell_order(instrument_uid: str, quantity_lots: int, price_rub: float, account_id: str) -> PostOrderResponse or None:
    try:
        with Client(TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            price_increment = utils.get_price_by_quotation(
                price=instruments.get_instrument_by_uid(uid=instrument_uid).min_price_increment
            )
            price = utils.get_quotation_by_price(math.ceil(price_rub / price_increment) * price_increment)

            if order := client.orders.post_order(
                instrument_id=instrument_uid,
                quantity=quantity_lots,
                price=price,
                account_id=account_id,
                order_type=OrderType.ORDER_TYPE_LIMIT,
                direction=OrderDirection.ORDER_DIRECTION_SELL,
            ):
                return order

    except Exception as e:
        logger.log_error(
            method_name='post_sell_order',
            error=e,
            debug_info=serializer.to_json({
                'instrument_name': instruments.get_instrument_by_uid(instrument_uid).name,
                'quantity_lots': quantity_lots,
                'price_rub': price_rub,
                'price_increment': price_increment,
                'price_quotation': price,
            }),
        )

    return None


def get_active_orders(instrument_uid: str, account_id: str) -> list[OrderState]:
    result = []

    try:
        with Client(TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            orders_resp = client.orders.get_orders(account_id=account_id)
            for order in (orders_resp.orders or []):
                if order.instrument_uid == instrument_uid:
                    result.append(order)
    except Exception as e:
        logger.log_error(method_name='users.get_active_orders', error=e)

    return result


@cache.ttl_cache(ttl=3600)
def get_user_instruments_list(account_id: str = None) -> list[Instrument]:
    result = []

    try:
        for instrument in instruments.get_instruments_white_list():
            if get_user_instrument_balance(instrument_uid=instrument.uid, account_id=account_id) > 0:
                result.append(instrument)

    except Exception as e:
        logger.log_error(method_name='get_user_instruments_list', error=e)

    return result


@cache.ttl_cache(ttl=3600)
def get_user_instrument_operations(instrument_figi: str, account_id: str = None) -> list[Operation]:
    result = []

    try:
        for account in get_accounts():
            if account_id is None or account.id == account_id:
                operations = get_operations(account_id=account.id, figi=instrument_figi)
                if operations and len(operations) > 0:
                    result.extend(operations)

    except Exception as e:
        logger.log_error(method_name='get_user_instrument_operations', error=e)

    return result


@cache.ttl_cache(ttl=3600 * 24, is_skip_empty=True)
def get_accounts() -> GetAccountsResponse.accounts:
    result = []

    try:
        with Client(TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            for a in client.users.get_accounts().accounts:
                if a.name in ['Основной', 'Аналитический']:
                    result.append(a)

    except Exception as e:
        logger.log_error(method_name='get_accounts', error=e)

    return result


def get_analytics_account() -> Account or None:
    if accounts := get_accounts():
        for a in accounts or []:
            if a.name == 'Аналитический':
                return a

    return None


@cache.ttl_cache(ttl=3600)
def get_portfolio(account_id: str):
    try:
        with Client(TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.operations.get_portfolio(account_id=account_id)

    except Exception as e:
        logger.log_error(method_name='get_portfolio', error=e)


@cache.ttl_cache(ttl=3600)
def get_positions(account_id: str) -> PositionsResponse or None:
    try:
        with Client(TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.operations.get_positions(account_id=str(account_id))

    except Exception as e:
        logger.log_error(method_name='get_positions', error=e)


@cache.ttl_cache(ttl=3600)
def get_operations(account_id: str, figi: str) -> list[Operation] or None:
    try:
        resp = list()

        with Client(TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            for operation in client.operations.get_operations(
                    account_id=account_id,
                    figi=figi,
                    state=OperationState.OPERATION_STATE_EXECUTED,
            ).operations:
                if (
                        operation.operation_type == OperationType.OPERATION_TYPE_SELL
                        or operation.operation_type == OperationType.OPERATION_TYPE_SELL_CARD
                        or operation.operation_type == OperationType.OPERATION_TYPE_BUY
                        or operation.operation_type == OperationType.OPERATION_TYPE_BUY_CARD
                ):
                    resp.append(operation)

        return resp

    except Exception as e:
        logger.log_error(method_name='get_operations', error=e)


def sort_instruments_by_balance(instruments_list: list[Instrument]) -> list[Instrument]:
    return sorted(instruments_list, key=get_instrument_total_balance_for_sort, reverse=True)


def sort_instruments_cost(instruments_list: list[Instrument], account_id: str or None) -> list[Instrument]:
    return sorted(
        instruments_list,
        key=lambda instrument: get_instrument_cost_for_sort(
            instrument_uid=instrument.uid,
            account_id=account_id,
        ),
        reverse=True,
    )


def sort_instruments_last_operation(instruments_list: list[Instrument], account_id: str or None) -> list[Instrument]:
    return sorted(
        instruments_list,
        key=lambda instrument: get_instrument_last_operation_seconds(
            instrument_figi=instrument.figi,
            account_id=account_id,
        ),
    )

def sort_instruments_by_volume_buy(instruments_list: list[Instrument]) -> list[Instrument]:
    return sorted(instruments_list, key=lambda i: _get_agent_rate(agent.volume.get_volume_buy_rate, i.uid), reverse=True)


def sort_instruments_by_volume_sell(instruments_list: list[Instrument]) -> list[Instrument]:
    return sorted(instruments_list, key=lambda i: _get_agent_rate(agent.volume.get_volume_sell_rate, i.uid), reverse=True)


def sort_instruments_by_macd_buy(instruments_list: list[Instrument]) -> list[Instrument]:
    return sorted(instruments_list, key=lambda i: _get_agent_rate(agent.macd.macd_buy_rate, i.uid), reverse=True)


def sort_instruments_by_macd_sell(instruments_list: list[Instrument]) -> list[Instrument]:
    return sorted(instruments_list, key=lambda i: _get_agent_rate(agent.macd.macd_sell_rate, i.uid), reverse=True)


def sort_instruments_by_rsi_buy(instruments_list: list[Instrument]) -> list[Instrument]:
    return sorted(instruments_list, key=lambda i: _get_agent_rate(agent.rsi.rsi_buy_rate, i.uid), reverse=True)


def sort_instruments_by_rsi_sell(instruments_list: list[Instrument]) -> list[Instrument]:
    return sorted(instruments_list, key=lambda i: _get_agent_rate(agent.rsi.rsi_sell_rate, i.uid), reverse=True)


def sort_instruments_by_tech_buy(instruments_list: list[Instrument]) -> list[Instrument]:
    return sorted(instruments_list, key=lambda i: _get_agent_rate(agent.tech.get_tech_buy_rate, i.uid), reverse=True)


def sort_instruments_by_tech_sell(instruments_list: list[Instrument]) -> list[Instrument]:
    return sorted(instruments_list, key=lambda i: _get_agent_rate(agent.tech.get_tech_sell_rate, i.uid), reverse=True)


def sort_instruments_by_news_buy(instruments_list: list[Instrument]) -> list[Instrument]:
    return sorted(instruments_list, key=lambda i: _get_agent_rate(agent.news.get_news_buy_rate, i.uid), reverse=True)


def sort_instruments_by_news_sell(instruments_list: list[Instrument]) -> list[Instrument]:
    return sorted(instruments_list, key=lambda i: _get_agent_rate(agent.news.get_news_sell_rate, i.uid), reverse=True)


def sort_instruments_by_fundamental_buy(instruments_list: list[Instrument]) -> list[Instrument]:
    return sorted(instruments_list, key=lambda i: _get_agent_rate(agent.fundamental.get_fundamental_buy_rate, i.uid), reverse=True)


def sort_instruments_by_fundamental_sell(instruments_list: list[Instrument]) -> list[Instrument]:
    return sorted(instruments_list, key=lambda i: _get_agent_rate(agent.fundamental.get_fundamental_sell_rate, i.uid), reverse=True)


def sort_instruments_by_profit_buy(instruments_list: list[Instrument], account_id: str) -> list[Instrument]:
    return sorted(
        instruments_list,
        key=lambda i: _get_agent_rate(agent.profit.get_profit_buy_rate, i.uid, account_id),
        reverse=True,
    )


def sort_instruments_by_profit_sell(instruments_list: list[Instrument], account_id: str) -> list[Instrument]:
    return sorted(
        instruments_list,
        key=lambda i: _get_agent_rate(agent.profit.get_profit_sell_rate, i.uid, account_id),
        reverse=True,
    )


def sort_instruments_by_total_rate_buy(instruments_list: list[Instrument], account_id: str) -> list[Instrument]:
    return sorted(
        instruments_list,
        key=lambda i: _get_agent_rate(agent.buy_sell_rate.get_total_buy_rate, i.uid, account_id),
        reverse=True,
    )


def sort_instruments_by_total_rate_sell(instruments_list: list[Instrument], account_id: str) -> list[Instrument]:
    return sorted(
        instruments_list,
        key=lambda i: _get_agent_rate(agent.buy_sell_rate.get_total_sell_rate, i.uid, account_id),
        reverse=True,
    )


def _get_agent_rate(rate_fn, instrument_uid: str, account_id: str = None) -> float:
    try:
        result = None
        if account_id:
            result = rate_fn(instrument_uid=instrument_uid, account_id=account_id)
        else:
            result = rate_fn(instrument_uid=instrument_uid)
        if result and result.get('rate') is not None:
            return result['rate']
    except Exception as e:
        logger.log_error(method_name='_get_agent_rate', error=e)
    return float('-inf')


@cache.ttl_cache(ttl=3600)
def get_instrument_total_balance_for_sort(instrument: Instrument) -> float:
    try:
        total_balance = get_user_instrument_balance(instrument_uid=instrument.uid)

        if total_balance > 0:
            last_price = instruments.get_instrument_last_price_by_uid(uid=instrument.uid)

            if last_price is not None and last_price > 0:
                return total_balance * last_price


    except Exception as e:
        logger.log_error(method_name='get_instrument_total_balance_for_sort', error=e)

    return float('-inf')


@cache.ttl_cache(ttl=3600)
def get_instrument_last_operation_seconds(instrument_figi: str, account_id: str) -> float:
    try:
        if operations := get_operations(account_id=account_id, figi=instrument_figi):
            now = datetime.datetime.now(pytz.utc)
            closest_operation = min(operations, key=lambda op: abs(now - op.date))
            time_diff = now - closest_operation.date

            return time_diff.total_seconds()

    except Exception as e:
        logger.log_error(method_name='get_instrument_last_operation_seconds', error=e)

    return float('inf')


@cache.ttl_cache(ttl=3600)
def get_instrument_cost_for_sort(instrument_uid: str, account_id: str) -> float:
    try:
        calc = invest_calc.get_invest_calc_by_instrument_uid(instrument_uid=instrument_uid, account_id=account_id)

        if calc and calc['market_value'] is not None:
            return calc['market_value']

    except Exception as e:
        logger.log_error(method_name='get_instrument_cost_for_sort', error=e)

    return float('-inf')


@cache.ttl_cache(ttl=3600)
def get_is_in_favorites(instrument_uid: str) -> bool:
    for i in instruments.get_favorites() or []:
        if i.uid == instrument_uid:
            return True

    return False


def generate_token(user_id: str) -> str or None:
    return utils.get_md5(f'{user_id}_{datetime.datetime.now()}_hash_salt_001_')


def get_user_by_login_password(login: str, password: str) -> db_2.users_db.UserDB or None:
    if user := db_2.users_db.get_user_by_login(login=login):
        if db_2.users_db.verify_password(password=password, hashed_password=user.password_hash):
            return user

    return None


def get_user_token(user_id: str) -> str or None:
    if user := db_2.users_db.get_user_by_id(user_id=user_id):
        if user.token:
            return user.token

        if generated_token := generate_token(user_id=user_id):
            db_2.users_db.update_user_token(user_id=user_id, token=generated_token)
            return generated_token

    return None
