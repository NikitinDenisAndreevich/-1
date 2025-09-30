import pytest
from datetime import datetime, timedelta
from src.reports import ReportService
import pandas as pd
import json
from pathlib import Path

def test_weekly_spending(sample_data):
    result = ReportService.get_weekly_spending(sample_data, '2024-01-10')
    assert 'weekly_distribution' in result
    assert 'Понедельник' in result['weekly_distribution']
    assert len(result['days_details']) == 10

def test_default_date(sample_data):
    result = ReportService.get_weekly_spending(sample_data)
    assert datetime.strptime(result['period']['end'], "%Y-%m-%d").date() == datetime.today().date()


@pytest.fixture
def sample_data():
    dates = pd.date_range(start='2024-01-01', periods=10).tolist()
    return pd.DataFrame({
        'date': dates,
        'category': ['еда'] * 5 + ['транспорт'] * 5,
        'amount': [1000, 1500, 2000, 500, 3000, 200, 200, 200, 200, 200]
    })

def test_valid_report(sample_data):
    result = ReportService.get_workday_weekend_spending(
        sample_data,
        'еда',
        '2024-01-01'
    )
    assert 'total_workdays' in result
    assert result['category'] == 'еда'
    assert len(result['daily_details']) == 5


def test_write_report_decorator(tmp_path, sample_data):
    # Проверим, что отчет сохраняется в файл по умолчанию (через декоратор)
    before = set(Path.cwd().iterdir())
    _ = ReportService.get_category_spending(sample_data, 'еда', '2024-01-01')
    after = set(Path.cwd().iterdir())
    created = list(after - before)
    assert any(p.suffix == '.json' and p.name.startswith('report_') for p in created)

def test_empty_data(sample_data):
    result = ReportService.get_workday_weekend_spending(
        sample_data,
        'несуществующая_категория',
        '2024-01-01'
    )
    assert 'error' in result

def test_category_spending(sample_data):
    result = ReportService.get_category_spending(
        sample_data,
        'еда',
        '2024-01-01'
    )
    assert result['total'] == 8000
    assert '2024-01' in result['monthly_breakdown']
    assert len(result['transactions']) == 5

def test_invalid_category(sample_data):
    result = ReportService.get_category_spending(
        sample_data,
        'несуществующая_категория',
        '2024-01-01'
    )
    assert 'error' in result