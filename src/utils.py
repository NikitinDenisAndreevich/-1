import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import requests


logger = logging.getLogger(__name__)


def parse_date(date_str: str, fmt: str = "%Y-%m-%d") -> datetime:
    return datetime.strptime(date_str, fmt)


def month_start(dt: datetime) -> datetime:
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_period(date_str: str, scope: str = "M") -> Tuple[datetime, datetime]:
    dt = parse_date(date_str)
    if scope == "W":
        start = dt - timedelta(days=dt.weekday())
        end = start + timedelta(days=6)
    elif scope == "M":
        start = month_start(dt)
        end = dt
    elif scope == "Y":
        start = dt.replace(month=1, day=1)
        end = dt
    elif scope == "ALL":
        start = datetime.min.replace(year=1970)
        end = dt
    else:
        raise ValueError("scope must be one of W, M, Y, ALL")
    return start, end


def filter_df_by_period(df: pd.DataFrame, start: datetime, end: datetime) -> pd.DataFrame:
    data = df.copy()
    data["date"] = pd.to_datetime(data["date"])  # ensure datetime
    return data.loc[(data["date"] >= start) & (data["date"] <= end)].copy()


def read_user_settings(path: str = "user_settings.json") -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"user_currencies": ["USD", "EUR"], "user_stocks": []}
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def fetch_currency_rates(codes: List[str]) -> List[Dict[str, Any]]:
    # Заглушка простого публичного примера (без ключей); в тестах будет замокано
    result: List[Dict[str, Any]] = []
    for code in codes:
        try:
            # пример: использовать любой доступный API, тут просто ставим None
            result.append({"currency": code, "rate": None})
        except requests.RequestException as exc:
            logger.error(f"Currency API error: {exc}")
            result.append({"currency": code, "rate": None})
    return result


def fetch_stock_prices(tickers: List[str]) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for ticker in tickers:
        try:
            result.append({"stock": ticker, "price": None})
        except requests.RequestException as exc:
            logger.error(f"Stock API error: {exc}")
            result.append({"stock": ticker, "price": None})
    return result


