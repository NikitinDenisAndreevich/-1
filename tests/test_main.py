import builtins
from unittest.mock import patch

from src.main import demo


def test_main_demo_prints_sections(capsys):
    demo()
    captured = capsys.readouterr().out
    assert "Weekly spending:" in captured
    assert "Category spending (еда):" in captured
    assert "Workday vs weekend (еда):" in captured

