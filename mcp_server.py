from mcp.server.fastmcp import FastMCP
from dataclasses import dataclass
from typing import List, Dict

# Создаём экземпляр сервера
mcp = FastMCP('TickerAnalysis')


# 📦 Ресурс: список всех компаний
@mcp.resource('ticker-analysis://list')
def list_companies() -> List[str]:
    return list()


@mcp.resource('ticker://{ticker}')
def get_company_info(ticker: str) -> dict:
    return {
        ticker: ticker,
    }

mcp.run()
