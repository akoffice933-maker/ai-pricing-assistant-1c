"""Конфигурация из окружения, логирование, fail-fast проверки при старте.

Не зависит от объекта FastAPI app — можно импортировать откуда угодно без
циклических зависимостей.
"""

import logging
import os
import sys

APP_VERSION = "2.2.0-production"
SERVICE_NAME = "AI Pricing Assistant — Market Demand MVP"

# ============================================================
# Окружение
# ============================================================
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
IS_PRODUCTION = ENVIRONMENT == "production"

API_TOKEN = os.getenv("AI_PRICING_API_TOKEN")
if IS_PRODUCTION and not API_TOKEN:
    # Отказываемся стартовать в production без токена — открытый API-эндпоинт,
    # считающий бизнес-цены, не должен быть доступен анонимно.
    raise RuntimeError(
        "AI_PRICING_API_TOKEN обязателен, когда ENVIRONMENT=production. "
        "Задайте переменную окружения перед запуском."
    )

_default_origins = ""
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("AI_PRICING_ALLOWED_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

RATE_LIMIT = os.getenv("AI_PRICING_RATE_LIMIT", "60/minute")

LOG_LEVEL = os.getenv("AI_PRICING_LOG_LEVEL", "INFO").upper()


def _origin_looks_valid(origin: str) -> bool:
    """Грубая проверка формата origin — ловит частые опечатки (нет схемы, лишний слэш, пробелы)."""
    if origin == "*":
        return True
    if not (origin.startswith("http://") or origin.startswith("https://")):
        return False
    if origin.endswith("/") or " " in origin:
        return False
    return True


# ============================================================
# Логирование
# ============================================================
logger = logging.getLogger("ai_pricing")
logger.setLevel(LOG_LEVEL)
if not logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(
        logging.Formatter(
            fmt='{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}',
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )
    logger.addHandler(_handler)

logger.info("startup environment=%s allowed_origins=%s", ENVIRONMENT, ALLOWED_ORIGINS or "(none)")
_invalid_origins = [o for o in ALLOWED_ORIGINS if not _origin_looks_valid(o)]
if _invalid_origins:
    logger.warning(
        "AI_PRICING_ALLOWED_ORIGINS содержит подозрительные значения (нет схемы http(s):// или "
        "лишний слэш/пробел): %s — браузер всё равно будет блокировать запросы с этих origin.",
        _invalid_origins,
    )
