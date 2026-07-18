"""Автотесты на fail-fast поведение при старте в ENVIRONMENT=production.

main.py выполняет эти проверки на уровне импорта модуля, поэтому единственный
надёжный способ их протестировать — реальный запуск в отдельном процессе
(monkeypatch os.environ здесь не сработает: main уже импортирован до теста).
"""

import subprocess
import sys


def _run_import_in_subprocess(env_overrides: dict, block_slowapi: bool = False) -> subprocess.CompletedProcess:
    code = (
        "import sys\n"
        + ("sys.modules['slowapi'] = None\n" if block_slowapi else "")
        + "import main\n"
        + "print('IMPORT_OK')\n"
    )
    import os

    env = os.environ.copy()
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=__file__.rsplit("/", 1)[0],
        env=env,
    )


def test_refuses_to_start_in_production_without_token():
    result = _run_import_in_subprocess({"ENVIRONMENT": "production", "AI_PRICING_API_TOKEN": ""})
    assert result.returncode != 0
    assert "AI_PRICING_API_TOKEN обязателен" in result.stderr


def test_starts_in_production_with_token():
    result = _run_import_in_subprocess({"ENVIRONMENT": "production", "AI_PRICING_API_TOKEN": "real-token"})
    assert result.returncode == 0
    assert "IMPORT_OK" in result.stdout


def test_refuses_to_start_in_production_without_slowapi():
    result = _run_import_in_subprocess(
        {"ENVIRONMENT": "production", "AI_PRICING_API_TOKEN": "real-token"},
        block_slowapi=True,
    )
    assert result.returncode != 0
    assert "slowapi не установлен" in result.stderr


def test_dev_mode_tolerates_missing_slowapi():
    result = _run_import_in_subprocess({"ENVIRONMENT": "development"}, block_slowapi=True)
    assert result.returncode == 0
    assert "IMPORT_OK" in result.stdout
