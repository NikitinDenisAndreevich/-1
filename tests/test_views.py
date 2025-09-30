import pandas as pd
import pytest
from unittest.mock import patch

from src.views import events_view


@pytest.fixture
def df_events():
    dates = pd.date_range(start='2024-01-01', periods=10).tolist()
    return pd.DataFrame({
        'date': dates,
        'category': ['Супермаркеты'] * 5 + ['Наличные'] * 2 + ['Переводы'] * 3,
        'amount': [1000, 1500, 2000, 500, 3000, 500, 200, 200, -1000, -2000],
    })


@patch('src.views.fetch_currency_rates', return_value=[{"currency": "USD", "rate": 73.0}])
@patch('src.views.fetch_stock_prices', return_value=[{"stock": "AAPL", "price": 150.0}])
def test_events_view_month(mock_stocks, mock_rates, df_events):
    res = events_view('2024-01-10', 'M', df_events)
    assert 'expenses' in res and 'income' in res
    assert res['currency_rates'][0]['currency'] == 'USD'
    assert res['stock_prices'][0]['stock'] == 'AAPL'
    assert res['expenses']['total_amount'] > 0
    assert res['income']['total_amount'] > 0


@pytest.mark.parametrize('scope', ['W', 'M', 'Y', 'ALL'])
@patch('src.views.fetch_currency_rates', return_value=[])
@patch('src.views.fetch_stock_prices', return_value=[])
def test_events_view_scopes(mock_stocks, mock_rates, scope, df_events):
    res = events_view('2024-01-10', scope, df_events)
    assert 'expenses' in res and 'income' in res

