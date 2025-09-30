"""Простой запускной модуль для демонстрации функционала отчетов."""

from datetime import datetime
import pandas as pd

from .reports import ReportService


def demo() -> None:
    dates = pd.date_range(start="2024-01-01", periods=10).tolist()
    df = pd.DataFrame({
        "date": dates,
        "category": ["еда"] * 5 + ["транспорт"] * 5,
        "amount": [1000, 1500, 2000, 500, 3000, 200, 200, 200, 200, 200],
    })

    print("Weekly spending:")
    print(ReportService.get_weekly_spending(df))

    print("\nCategory spending (еда):")
    print(ReportService.get_category_spending(df, "еда", "2024-01-01"))

    print("\nWorkday vs weekend (еда):")
    print(ReportService.get_workday_weekend_spending(df, "еда", "2024-01-01"))


if __name__ == "__main__":
    demo()

