import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Callable
import json
import pandas as pd
try:
    from workalendar.europe import Russia
except Exception:
    Russia = None


def write_report(filename: Optional[str] = None) -> Callable[[Callable[..., Dict[str, Any]]], Callable[..., Dict[str, Any]]]:
    """Декоратор: записывает результат функции-отчета в JSON-файл.

    Если filename не указан, используется имя по умолчанию вида report_YYYYMMDD_HHMMSS.json.
    """
    def decorator(func: Callable[..., Dict[str, Any]]) -> Callable[..., Dict[str, Any]]:
        def wrapper(*args: Any, **kwargs: Any) -> Dict[str, Any]:
            result = func(*args, **kwargs)
            out_name = filename or f"report_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
            try:
                with open(out_name, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            except Exception as exc:  # логируем, но не прерываем возврат результата
                logging.getLogger(__name__).error(f"Ошибка записи отчета в файл: {exc}")
            return result
        return wrapper
    return decorator


class ReportService:
    """Сервис формирования отчетов."""

    @staticmethod
    @write_report()  # запись в файл по умолчанию
    def get_category_spending(
        df: pd.DataFrame, category: str, period_start: str
    ) -> Dict[str, Any]:
        """Возвращает агрегированные траты по категории за 3 месяца от `period_start`.

        Ожидаются колонки датафрейма: `date` (datetime/str), `category` (str), `amount` (number).
        """
        logger = logging.getLogger(__name__)
        logger.info(f"Старт отчета по категории: {category}")
        try:
            start_date = datetime.strptime(period_start, "%Y-%m-%d")
            end_date = start_date + timedelta(days=90)

            mask = (df["category"] == category) & (df["date"] >= start_date) & (df["date"] <= end_date)
            filtered = df.loc[mask].copy()
            if filtered.empty:
                return {"error": f"Нет данных по категории '{category}'"}

            filtered["date"] = pd.to_datetime(filtered["date"])
            filtered["month"] = filtered["date"].dt.strftime("%Y-%m")

            monthly = filtered.groupby("month")["amount"].sum().to_dict()
            transactions = filtered[["date", "amount"]].to_dict("records")
            for t in transactions:
                t["date"] = t["date"].strftime("%Y-%m-%d")

            return {
                "category": category,
                "period": {"start": period_start, "end": end_date.strftime("%Y-%m-%d")},
                "total": float(filtered["amount"].sum()),
                "monthly_breakdown": monthly,
                "transactions": transactions,
            }
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Ошибка: {str(exc)}", exc_info=True)
            return {"error": "Internal Server Error"}

    @staticmethod
    @write_report()  # запись в файл по умолчанию
    def get_weekly_spending(df: pd.DataFrame, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Возвращает распределение трат по дням недели за последние 90 дней до `end_date`.

        Если `end_date` не передана — используется текущая дата.
        Ожидаются колонки: `date`, `amount`.
        """
        logger = logging.getLogger(__name__)
        logger.info("Старт отчета: траты по дням недели")
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()
            start_dt = end_dt - timedelta(days=90)

            mask = (df["date"] >= start_dt) & (df["date"] <= end_dt)
            filtered = df.loc[mask].copy()

            # Локально-независимые русские названия дней недели
            ru_weekdays = [
                "Понедельник",
                "Вторник",
                "Среда",
                "Четверг",
                "Пятница",
                "Суббота",
                "Воскресенье",
            ]
            if filtered.empty:
                weekly_zero = {day: 0 for day in ru_weekdays}
                return {
                    "period": {"start": start_dt.strftime("%Y-%m-%d"), "end": end_dt.strftime("%Y-%m-%d")},
                    "total": 0.0,
                    "weekly_distribution": weekly_zero,
                    "days_details": [],
                }

            filtered["date"] = pd.to_datetime(filtered["date"])  # ensure datetime
            filtered["day_of_week"] = filtered["date"].dt.weekday.map(lambda i: ru_weekdays[int(i)])

            daily = filtered.groupby(["date", "day_of_week"], as_index=False)["amount"].sum()
            weekly = daily.groupby("day_of_week")["amount"].sum().to_dict()

            return {
                "period": {"start": start_dt.strftime("%Y-%m-%d"), "end": end_dt.strftime("%Y-%m-%d")},
                "total": float(daily["amount"].sum()),
                "weekly_distribution": weekly,
                "days_details": [
                    {
                        "date": row["date"].strftime("%Y-%m-%d"),
                        "day_of_week": row["day_of_week"],
                        "amount": row["amount"],
                    }
                    for _, row in daily.iterrows()
                ],
            }
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Ошибка: {str(exc)}", exc_info=True)
            return {"error": "Internal Server Error"}

    @staticmethod
    @write_report()  # запись в файл по умолчанию
    def get_workday_weekend_spending(
        df: pd.DataFrame, category: str, period_start: str
    ) -> Dict[str, Any]:
        """Возвращает суммы трат по категории в рабочие и выходные за 3 месяца от `period_start`.

        Ожидаются колонки: `date`, `category`, `amount`.
        """
        logger = logging.getLogger(__name__)
        logger.info("Старт генерации отчета: рабочие/выходные дни")
        try:
            start_date = datetime.strptime(period_start, "%Y-%m-%d")
            end_date = start_date + timedelta(days=90)

            mask = (df["category"] == category) & (df["date"] >= start_date) & (df["date"] <= end_date)
            filtered = df.loc[mask].copy()
            if filtered.empty:
                return {"error": "Нет данных за указанный период"}

            filtered["date"] = pd.to_datetime(filtered["date"]).dt.date
            daily = filtered.groupby("date", as_index=False)["amount"].sum()

            cal = Russia() if Russia else None
            def is_workday(d):
                # Рабочий день только пн-пт и не праздничный по календарю
                if d.weekday() >= 5:
                    return False
                try:
                    if cal is None:
                        return True
                    return bool(cal.is_working_day(d))
                except Exception:
                    return True

            daily["is_workday"] = daily["date"].apply(is_workday)

            return {
                "category": category,
                "period": {"start": period_start, "end": end_date.strftime("%Y-%m-%d")},
                "total_workdays": float(daily.query("is_workday")["amount"].sum()),
                "total_weekends": float(daily.query("not is_workday")["amount"].sum()),
                "daily_details": [
                    {
                        "date": row["date"].strftime("%Y-%m-%d"),
                        "is_workday": row["is_workday"],
                        "amount": row["amount"],
                    }
                    for _, row in daily.iterrows()
                ],
            }
        except Exception as exc:
            logger.error(f"Ошибка: {str(exc)}", exc_info=True)
            return {"error": "Internal Server Error"}
