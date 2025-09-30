import pytest
from src.services import SearchService, investment_bank

@pytest.fixture
def sample_transactions():
    return [
        {'description': 'Покупка', 'amount': 1000},
        {'description': 'Перевод', 'amount': 500}
    ]

def test_simple_search(sample_transactions):
    result = SearchService.simple_search('Покупка', sample_transactions)
    assert len(result['results']) == 1


@pytest.mark.parametrize("limit,expected", [
    (10, 6.0),  # 1000->0, 500->0; добавим еще покупки для демонстрации ниже
    (50, 0.0),
    (100, 0.0),
])
def test_investment_bank_basic(limit, expected):
    txs = [
        {"Дата операции": "2024-01-05", "Сумма операции": 1000.0},
        {"Дата операции": "2024-01-10", "Сумма операции": 500.0},
        {"Дата операции": "2024-02-10", "Сумма операции": 123.0},  # другой месяц
        {"Дата операции": "2024-01-15", "Сумма операции": -200.0},  # не учитываем поступления/возвраты
        {"Дата операции": "bad-date", "Сумма операции": 300.0},     # пропуск некорректных
    ]
    # Для 2024-01: 1000 и 500. При limit=10 остатки 0 и 0 => 0, но добавим дробные, чтобы проверить округление
    # Корректируем ожидания: добавим третью покупку в январе для округления
    txs.append({"Дата операции": "2024-01-20", "Сумма операции": 123.0})
    # 123 при limit=10 => 7
    # Итого ожидаем 7.0 для limit=10, 27.0 для limit=50, 77.0 для limit=100
    calc = investment_bank("2024-01", txs, limit)
    if limit == 10:
        assert calc == 7.0
    elif limit == 50:
        assert calc == 27.0
    else:
        assert calc == 77.0
