import datetime
import multiprocessing
import resource
import io
import textwrap
import traceback
from langchain_core.tools import tool
from contextlib import redirect_stdout
from RestrictedPython import compile_restricted
from RestrictedPython.Guards import safe_builtins
from lib import instruments, fundamentals, predictions, users, invest_calc, news, agent, db_2, logger

TIME_LIMIT = 2          # сек
MEM_LIMIT_MB = 64       # МБ
MEM_LIMIT = MEM_LIMIT_MB * 1024 * 1024


@tool
def get_instruments_list() -> list[str]:
    """
    Получает список UID биржевых активов
    """
    return [instrument.uid for instrument in instruments.get_instruments_white_list()][:10]


@tool
def get_user_instruments_list() -> list[str]:
    """
    Возвращает список UID биржевых активов, которые есть в портфеле
    """
    return [instrument.uid for instrument in users.get_user_instruments_list()]


@tool
def get_instrument_info(uid: str) -> dict or None:
    """
    Возвращает подробную информацию о единичном биржевом активе. На выходе: фундаментальные показатели, текущая цена, прогноз изменения цены, оценка новостного фона относительно актива. На входе: UID актива.
    """
    instrument_uid = uid

    if instrument_info := instruments.get_instrument_by_uid(uid=instrument_uid):
        fundamentals_resp = fundamentals.get_fundamentals_by_asset_uid(asset_uid=instrument_info.asset_uid)
        fundamentals_info = fundamentals_resp[0] if fundamentals_resp and len(fundamentals_resp) > 0 else None
        price = instruments.get_instrument_last_price_by_uid(uid=instrument_uid)
        now = datetime.datetime.now(datetime.timezone.utc)
        prediction_7 = predictions.get_relative_predictions_consensus(
            instrument_uid=instrument_uid,
            date_target=now + datetime.timedelta(days=7)
        )
        prediction_30 = predictions.get_relative_predictions_consensus(
            instrument_uid=instrument_uid,
            date_target=now + datetime.timedelta(days=30)
        )
        prediction_60 = predictions.get_relative_predictions_consensus(
            instrument_uid=instrument_uid,
            date_target=now + datetime.timedelta(days=60)
        )
        prediction_90 = predictions.get_relative_predictions_consensus(
            instrument_uid=instrument_uid,
            date_target=now + datetime.timedelta(days=90)
        )
        prediction_180 = predictions.get_relative_predictions_consensus(
            instrument_uid=instrument_uid,
            date_target=now + datetime.timedelta(days=180)
        )
        prediction_365 = predictions.get_relative_predictions_consensus(
            instrument_uid=instrument_uid,
            date_target=now + datetime.timedelta(days=365)
        )

        return {
            'fundamentals': {
                'currency': fundamentals_info.currency,
                'revenue_ttm': fundamentals_info.revenue_ttm,
                'ebitda_ttm': fundamentals_info.ebitda_ttm,
                'market_capitalization': fundamentals_info.market_capitalization,
                'total_debt_mrq': fundamentals_info.total_debt_mrq,
                'eps_ttm': fundamentals_info.eps_ttm,
                'pe_ratio_ttm': fundamentals_info.pe_ratio_ttm,
                'ev_to_ebitda_mrq': fundamentals_info.ev_to_ebitda_mrq,
                'dividend_payout_ratio_fy': fundamentals_info.dividend_payout_ratio_fy,
            },
            'current_price': price,
            'price_relative_change_prediction_future_days': [
                {
                    '7': prediction_7,
                    '30': prediction_30,
                    '60': prediction_60,
                    '90': prediction_90,
                    '180': prediction_180,
                    '365': prediction_365,
                }
            ],
            'news_sentiment_last_month': news.news.get_influence_score(
                instrument_uid=instrument_uid,
                start_date=datetime.datetime.now() - datetime.timedelta(days=30),
                end_date=datetime.datetime.now(),
            ),
            'ticker': instrument_info.ticker,
            'full_name': instrument_info.name,
        }
    return None


@tool
def get_instrument_balance(uid: str) -> dict or None:
    """
    Возвращает баланс единичного биржевого актива. На выходе: баланс актива в портфеле, среднюю цена покупки, потенциальная прибыль, рыночная стоимость. На входе: UID актива.
    """
    instrument_uid = uid

    if balance := users.get_user_instrument_balance(instrument_uid=instrument_uid, account_id=users.get_analytics_account().id):
        if invest_calc_info := invest_calc.get_invest_calc_by_instrument_uid(instrument_uid=instrument_uid):
            return {
                'balance': balance,
                'market_value': invest_calc_info['market_value'],
                'potential_profit': invest_calc_info['potential_profit'],
                'potential_profit_percent': invest_calc_info['potential_profit_percent'],
                'avg_price': invest_calc_info['avg_price'],
            }
    return None


def _sandbox_runner(src: str, queue):
    """Запуск кода в изолированном процессе."""
    try:
        # 1) Ограничиваем ресурсы
        resource.setrlimit(resource.RLIMIT_AS, (MEM_LIMIT, MEM_LIMIT))  # память
        # 2) Компилируем с RestrictedPython
        byte_code = compile_restricted(textwrap.dedent(src), "<agent>", "exec")
        env = {"__builtins__": safe_builtins}
        buf = io.StringIO()
        with redirect_stdout(buf):
            exec(byte_code, env, {})
        queue.put(agent.models.PythonExecutionResult(ok=True, output=buf.getvalue()))
    except Exception as e:
        queue.put(
            agent.models.PythonExecutionResult(
                ok=False,
                output="Ошибка: " + "".join(traceback.format_exception_only(type(e), e)).strip()
            )
        )


@tool
def run_python_code(code: str) -> dict:
    """
    Безопасно выполняет фрагмент Python 3.11.
    """
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=_sandbox_runner, args=(code, q))
    p.start()
    p.join(TIME_LIMIT)

    if p.is_alive():
        p.terminate()
        return agent.models.PythonExecutionResult(ok=False, output='Ошибка: превышен лимит времени').model_dump()

    try:
        result: agent.models.PythonExecutionResult = q.get_nowait()
        return result.dict()
    except Exception as e:
        print('ERROR run_python_code', e)
        return agent.models.PythonExecutionResult(ok=False, output='Неизвестная ошибка выполнения').model_dump()


@tool
def get_instrument_buy_rate(instrument_uid: str) -> dict or None:
    """
    Возвращает оценку привлекательности покупки биржевого актива для последующей выгодной продажи.
    На выходе: оценка привлекательности от 0 до 100.
    На входе: UID актива.
    """
    try:
        if tag := db_2.instrument_tags_db.get_tag(instrument_uid=instrument_uid, tag_name='llm_buy_rate'):
            if tag_value := tag.tag_value:
                return tag_value
    except Exception as e:
        logger.log_error(
            method_name='get_instrument_buy_rate',
            error=e,
            is_telegram_send=False,
        )

    return None
