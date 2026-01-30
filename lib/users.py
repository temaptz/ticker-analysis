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
    Account, PostOrderResponse, OrderType, OrderDirection,
)
from const import TINKOFF_INVEST_TOKEN
from lib import cache, instruments, utils, logger, invest_calc, predictions, db_2, agent, serializer


@cache.ttl_cache(ttl=3600)
def get_user_instrument_balance(instrument_uid: str, account_id: int = None) -> int:
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


def get_user_money_rub() -> int:
    result = 0

    try:
        if account := get_analytics_account():
            if positions := get_positions(account_id=account.id):
                if positions.money and len(positions.money) > 0:
                    for m in positions.money:
                        if m.currency == 'rub':
                            result += utils.get_price_by_quotation(m)
                    for b in positions.blocked:
                        if b.currency == 'rub':
                            result -= utils.get_price_by_quotation(b)

    except Exception as e:
        logger.log_error(method_name='get_user_money_rub', error=e)

    return result


def post_buy_order(instrument_uid: str, quantity_lots: int, price_rub: float) -> PostOrderResponse or None:
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
                account_id=get_analytics_account().id,
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


def post_sell_order(instrument_uid: str, quantity_lots: int, price_rub: float) -> PostOrderResponse or None:
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
                account_id=get_analytics_account().id,
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


@cache.ttl_cache(ttl=3600)
def get_user_instruments_list(account_id: int = None) -> list[Instrument]:
    result = []

    try:
        for instrument in instruments.get_instruments_white_list():
            if get_user_instrument_balance(instrument_uid=instrument.uid, account_id=account_id) > 0:
                result.append(instrument)

    except Exception as e:
        logger.log_error(method_name='get_user_instruments_list', error=e)

    return result


@cache.ttl_cache(ttl=3600)
def get_user_instrument_operations(instrument_figi: str, account_id: int = None) -> list[Operation]:
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


@cache.ttl_cache(ttl=3600 * 24)
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
def get_positions(account_id: int) -> PositionsResponse or None:
    try:
        with Client(TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.operations.get_positions(account_id=account_id)

    except Exception as e:
        logger.log_error(method_name='get_positions', error=e)


@cache.ttl_cache(ttl=3600)
def get_operations(account_id: int, figi: str) -> list[Operation] or None:
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


def sort_instruments_for_buy(instruments_list: list[Instrument]) -> list[Instrument]:
    return sorted(instruments_list, key=get_instrument_buy_rate_for_sort, reverse=True)


def sort_instruments_for_sell(instruments_list: list[Instrument]) -> list[Instrument]:
    return sorted(instruments_list, key=get_instrument_sell_rate_for_sort, reverse=True)


def sort_instruments_cost(instruments_list: list[Instrument]) -> list[Instrument]:
    return sorted(instruments_list, key=get_instrument_cost_for_sort, reverse=True)


def sort_instruments_last_operation(instruments_list: list[Instrument]) -> list[Instrument]:
    return sorted(instruments_list, key=get_instrument_last_operation_seconds, reverse=False)


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
def get_instrument_sell_rate_for_sort(instrument: Instrument) -> float:
    try:
        if tag := db_2.instrument_tags_db.get_tag(instrument_uid=instrument.uid, tag_name='llm_sell_rate'):
            if tag_value := tag.tag_value:
                return int(tag_value)

    except Exception as e:
        logger.log_error(method_name='get_instrument_sell_rate_for_sort', error=e)

    return float('-inf')


@cache.ttl_cache(ttl=3600)
def get_instrument_buy_rate_for_sort(instrument: Instrument) -> float:
    try:
        if tag := db_2.instrument_tags_db.get_tag(instrument_uid=instrument.uid, tag_name='llm_buy_rate'):
            if tag_value := tag.tag_value:
                return int(tag_value)

    except Exception as e:
        logger.log_error(method_name='get_instrument_buy_rate_for_sort', error=e)

    return float('-inf')


@cache.ttl_cache(ttl=3600)
def get_instrument_last_operation_seconds(instrument: Instrument) -> float:
    try:
        if operations := get_operations(account_id=get_analytics_account().id, figi=instrument.figi):
            now = datetime.datetime.now(pytz.utc)
            closest_operation = min(operations, key=lambda op: abs(now - op.date))
            time_diff = now - closest_operation.date

            return time_diff.total_seconds()

    except Exception as e:
        logger.log_error(method_name='get_instrument_last_operation_seconds', error=e)

    return float('inf')


@cache.ttl_cache(ttl=3600)
def get_instrument_cost_for_sort(instrument: Instrument) -> float:
    try:
        calc = invest_calc.get_invest_calc_by_instrument_uid(instrument_uid=instrument.uid, account_id=get_analytics_account().id)

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
