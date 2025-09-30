Проект для анализа банковских транзакций из Excel с генерацией JSON-данных и отчетов.

Структура
---------

```
src/
  utils.py
  services.py
  reports.py
  main.py
tests/
  test_reports.py
  test_services.py
data/
  operations.xlsx
```

Требования
----------
- Python 3.8+
- Poetry

Установка
---------
```
poetry install
```

Запуск тестов
-------------
```
pytest -q
```

Покрытие тестами
-----------------
```
pytest --cov=src --cov-report=term-missing -q
```

Запуск модуля
-------------
```
python -m src.main
```

Настройки
---------
- Переменные окружения в `.env` (см. `.env_template`).
- Пользовательские настройки в `user_settings.json`.
