import json
import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from .utils import (
    fetch_currency_rates,
    fetch_stock_prices,
    filter_df_by_period,
    get_period,
    read_user_settings,
)
logger = logging.getLogger(__name__)


def _build_top_categories(df_part: pd.DataFrame, top_n: int = 7) -> List[Dict[str, Any]]:
    if df_part.empty:
        return []
    agg = (
        df_part.groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
    )
    head = agg.head(top_n)
    tail_sum = agg["amount"].iloc[top_n:].sum()
    items = [{"category": r["category"], "amount": int(round(r["amount"]))} for _, r in head.iterrows()]
    if tail_sum > 0:
        items.append({"category": "Остальное", "amount": int(round(tail_sum))})
    return items


def events_view(date_str: str, scope: str = "M", df: Optional[pd.DataFrame] = None) -> str:
    """Функция страницы «События».

    Args:
        date_str: Дата в формате YYYY-MM-DD.
        scope: W|M|Y|ALL — период.
        df: DataFrame транзакций (если None — ошибка).

    Returns:
        JSON-строка по ТЗ: расходы (total, main, transfers_and_cash), доходы (total, main),
        а также курсы валют и цены акций по пользовательским настройкам.
    """
    if df is None:
        raise ValueError("DataFrame is required")

    logger.info("События: расчет агрегатов")
    start, end = get_period(date_str, scope)
    data = filter_df_by_period(df, start, end)

    # Округление сумм до целых
    data = data.copy()
    if not pd.api.types.is_datetime64_any_dtype(data["date"]):
        data["date"] = pd.to_datetime(data["date"])  # ensure datetime

    # Определим расход/доход по знаку amount: предполагаем, что доходы >=0, расходы >0 по доменной модели
    # Для совместимости с ТЗ: используем category для сегментов переводов/наличных
    expenses_df = data[data["amount"] > 0]
    income_df = data[data["amount"] <= 0].assign(amount=lambda x: x["amount"].abs())

    expenses_total = int(round(expenses_df["amount"].sum())) if not expenses_df.empty else 0
    expenses_main = _build_top_categories(expenses_df)
    transfers_categories = ["Наличные", "Переводы"]
    transfers_and_cash = (
        expenses_df[expenses_df["category"].isin(transfers_categories)]
        .groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
    )
    transfers_and_cash_list = [
        {"category": r["category"], "amount": int(round(r["amount"]))} for _, r in transfers_and_cash.iterrows()
    ]

    income_total = int(round(income_df["amount"].sum())) if not income_df.empty else 0
    income_main = _build_top_categories(income_df, top_n=7)

    settings = read_user_settings()
    currency_rates = fetch_currency_rates(settings.get("user_currencies", []))
    stock_prices = fetch_stock_prices(settings.get("user_stocks", []))

    payload = {
        "expenses": {
            "total_amount": expenses_total,
            "main": expenses_main,
            "transfers_and_cash": transfers_and_cash_list,
        },
        "income": {
            "total_amount": income_total,
            "main": income_main,
        },
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }

    return json.dumps(payload, ensure_ascii=False)
