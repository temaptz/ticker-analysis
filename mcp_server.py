from fastmcp import FastMCP
from lib import users
import fast_api

mcp = FastMCP('TickerAnalysis')

@mcp.tool(
    description='Getting list of user accounts',
    tags={'list', 'accounts'},
)
def get_accounts():
    return fast_api.accounts_endpoint()


@mcp.tool(
    description='Getting list of instruments sorted by best for buy',
    tags={'list', 'instruments', 'buy'},
)
def get_instruments_to_buy(account_id: str, limit: int):
    return fast_api.instruments_list(sort=19, account_id=account_id)[:limit]


@mcp.tool(
    description='Getting list of instruments sorted by best for sell',
    tags={'list', 'instruments', 'sell'},
)
def get_instruments_to_sell(account_id: str, limit: int):
    return fast_api.instruments_list(sort=20, account_id=account_id)[:limit]


@mcp.tool(
    description='Getting instrument buy rate',
    tags={'rate', 'instruments', 'buy'},
)
def get_instrument_buy_rate(instrument_uid: str, account_id: str):
    return fast_api.instrument_buy_sell_total_rate(
        instrument_uid=instrument_uid,
        account_id=account_id,
        is_buy=True,
    )


@mcp.tool(
    description='Getting instrument sell rate',
    tags={'rate', 'instruments', 'sell'},
)
def get_instrument_sell_rate(instrument_uid: str, account_id: str):
    return fast_api.instrument_buy_sell_total_rate(
        instrument_uid=instrument_uid,
        account_id=account_id,
        is_buy=False,
    )
