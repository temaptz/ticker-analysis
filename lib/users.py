from tinkoff.invest import (
    Client,
    constants,
    GetAccountsResponse,
    PositionsResponse,
    Operation,
    OperationState
)
from const import TINKOFF_INVEST_TOKEN
from lib import cache


@cache.ttl_cache(ttl=3600)
def get_user_instrument_balance(account_name: str, instrument_uid: str) -> int:
    try:
        for account in get_accounts():
            if account.name == account_name:
                positions = get_positions(account_id=account.id)
                for instrument in positions.securities:
                    if instrument.instrument_uid == instrument_uid:
                        return instrument.balance

    except Exception as e:
        print('ERROR', e)


@cache.ttl_cache(ttl=3600)
def get_user_instrument_operations(account_name: str, instrument_figi: str) -> list[Operation]:
    try:
        for account in get_accounts():
            if account.name == account_name:
                return get_operations(account_id=account.id, figi=instrument_figi)

    except Exception as e:
        print('ERROR', e)


@cache.ttl_cache(ttl=3600)
def get_accounts() -> GetAccountsResponse.accounts:
    cache_key = 'get_accounts'
    try:
        c = cache.cache_get(cache_key)
        if c:
            return c

        with Client(TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            result = client.users.get_accounts().accounts

            if result:
                cache.cache_set(cache_key, result)

            return result

    except Exception as e:
        print('ERROR get_accounts', e)


@cache.ttl_cache(ttl=3600)
def get_portfolio(account_id: str):
    try:
        with Client(TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.operations.get_portfolio(account_id=account_id)

    except Exception as e:
        print('ERROR get_portfolio', e)


@cache.ttl_cache(ttl=3600)
def get_positions(account_id: str) -> PositionsResponse:
    try:
        with Client(TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.operations.get_positions(account_id=account_id)

    except Exception as e:
        print('ERROR get_positions', e)


def get_operations(account_id: str, figi: str) -> list[Operation]:
    try:
        resp = list()

        with Client(TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            for operation in client.operations.get_operations(account_id=account_id, figi=figi).operations:
                if operation.state == OperationState.OPERATION_STATE_EXECUTED:
                    resp.append(operation)

        return resp

    except Exception as e:
        print('ERROR get_operations', e)
