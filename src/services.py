import logging
import re
from typing import Any, Dict, List
from datetime import datetime


logger = logging.getLogger(__name__)


class SearchService:
    """Сервисы поиска по транзакциям."""

    @staticmethod
    def simple_search(query: str, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ищет транзакции, содержащие запрос в описании или категории.

        Args:
            query: Строка запроса (регистр игнорируется).
            transactions: Список транзакций.

        Returns:
            Словарь с ключом "results" и списком найденных транзакций.
        """
        logger.info("Запуск простого поиска")
        normalized_query = (query or "").strip().lower()
        if not normalized_query:
            return {"results": []}

        def matches(transaction: Dict[str, Any]) -> bool:
            description = str(transaction.get("description", "")).lower()
            category = str(transaction.get("category", "")).lower()
            return normalized_query in description or normalized_query in category

        results = [t for t in transactions if matches(t)]
        return {"results": results}

    @staticmethod
    def phone_search(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Находит транзакции, содержащие российские мобильные номера в описании.

        Поддерживаемые форматы: +7 9XX XXX-XX-XX, +7 9XXXXXXXXX, 8 9XX XXX XX XX и т.п.

        Args:
            transactions: Список транзакций.

        Returns:
            Словарь с ключом "results" и списком найденных транзакций.
        """
        logger.info("Поиск по телефонным номерам")
        phone_pattern = re.compile(
            r"(?:\+7|8)\s?(?:\(?(9\d{2})\)?)[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}",
            re.UNICODE,
        )

        def contains_phone(transaction: Dict[str, Any]) -> bool:
            description = str(transaction.get("description", ""))
            return bool(phone_pattern.search(description))

        results = [t for t in transactions if contains_phone(t)]
        return {"results": results}


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    """Рассчитывает сумму для «Инвесткопилки» за указанный месяц.

    Округляет каждую расходную операцию (отрицательные/положительные траты?) до ближайшего шага `limit`
    вверх и суммирует разницу между округленной суммой и фактической.

    Args:
        month: Строка в формате 'YYYY-MM'.
        transactions: Список транзакций c ключами 'Дата операции' (YYYY-MM-DD) и 'Сумма операции' (float).
        limit: Шаг округления (10, 50, 100).

    Returns:
        Итоговая сумма, которая попала бы в «Инвесткопилку».
    """
    logger.info("Расчет Инвесткопилки")
    if limit not in {10, 50, 100}:
        raise ValueError("limit должен быть одним из {10, 50, 100}")

    try:
        target_year, target_month = map(int, month.split("-"))
    except Exception as exc:
        raise ValueError("month должен быть в формате 'YYYY-MM'") from exc

    total_saved: float = 0.0

    for tx in transactions:
        try:
            date_str = str(tx.get("Дата операции", ""))
            amount = float(tx.get("Сумма операции", 0))
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            continue

        if date_obj.year != target_year or date_obj.month != target_month:
            continue

        # Считаем только расходы: положительные суммы покупок (как в Т-Банке)
        if amount <= 0:
            continue

        remainder = amount % limit
        if remainder == 0:
            increment = 0.0
        else:
            increment = limit - remainder
        total_saved += increment

    return round(float(total_saved), 2)
