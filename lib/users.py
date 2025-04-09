from tinkoff.invest import (
    Client,
    constants,
    GetAccountsResponse,
    PositionsResponse,
    Operation,
    OperationState,
    OperationType,
    Instrument,
)
from const import TINKOFF_INVEST_TOKEN
from lib import cache, instruments, utils, logger


@cache.ttl_cache(ttl=3600)
def get_user_instrument_balance(instrument_uid: str) -> int:
    result = 0

    try:
        for account in get_accounts():
            positions = get_positions(account_id=account.id)
            for instrument in positions.securities:
                if instrument.instrument_uid == instrument_uid:
                    result += instrument.balance

    except Exception as e:
        logger.log_error(method_name='get_user_instrument_balance', error=e)

    return result


@cache.ttl_cache(ttl=3600)
def get_user_instrument_operations(instrument_figi: str) -> list[Operation]:
    result = []

    try:
        for account in get_accounts():
            operations = get_operations(account_id=account.id, figi=instrument_figi)
            if operations and len(operations) > 0:
                result.extend(operations)

    except Exception as e:
        logger.log_error(method_name='get_user_instrument_operations', error=e)

    return result


@cache.ttl_cache(ttl=3600)
def get_accounts() -> GetAccountsResponse.accounts:
    try:
        with Client(TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.users.get_accounts().accounts

    except Exception as e:
        logger.log_error(method_name='get_accounts', error=e)


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
            return client.operations.get_positions(account_id=account_id)

    except Exception as e:
        logger.log_error(method_name='get_positions', error=e)


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


def get_instrument_total_balance_for_sort(instrument: Instrument) -> float:
    try:
        total_balance = get_user_instrument_balance(instrument_uid=instrument.uid)

        if total_balance > 0:
            last_prices = instruments.get_instrument_last_price_by_uid(uid=instrument.uid)

            if last_prices and last_prices[0]:
                current_price = utils.get_price_by_quotation(last_prices[0].price)

                if current_price and current_price > 0:
                    return total_balance * current_price

    except Exception as e:
        logger.log_error(method_name='get_instrument_total_balance_for_sort', error=e)

    return 0
