"""
AI Pricing Market MVP
==============
Точка входа для uvicorn/тестов/скриптов.

Реальная сборка приложения — в пакете app/ (см. app/server.py). main.py остаётся
на этом же месте и с этим же именем ради обратной совместимости:

    uvicorn main:app --reload --port 8000
    from main import app

Документация: http://localhost:8000/docs

Главный принцип архитектуры:
    Мы НЕ прогнозируем цену напрямую.
    Мы прогнозируем спрос при разных ценах относительно рынка, затем оптимизируем цену
    под бизнес-цель и ограничения.
"""

from app.server import app

# Некоторые скрипты (scripts/backtest_elasticity.py), тесты и старые примеры импортируют
# схемы/skills/config напрямую из main — оставляем реэкспорт для обратной совместимости.
# ВАЖНО: config реэкспортирован как МОДУЛЬ (не отдельные имена), потому что тесты делают
# monkeypatch.setattr(main.config, "API_TOKEN", ...) — это работает только через атрибут
# модуля, а не через скопированное `from app.config import API_TOKEN` имя.
from app import config  # noqa: F401
from app.config import _origin_looks_valid  # noqa: F401 - чистая функция, безопасно реэкспортировать напрямую
from app.schemas import (  # noqa: F401
    BusinessGoal,
    DemandCurveRequest,
    DemandCurveResponse,
    ItemData,
    ItemType,
    MarketContext,
    MarketIndicatorsCalculationRequest,
    MarketIndicatorsCalculationResponse,
    PriceOptimizationRequest,
    PriceOptimizationResponse,
    PriceRecommendationRequest,
    PriceRecommendationResponse,
    PriceUnit,
)
from app.services.market_indicators import calculate_market_context_from_observations  # noqa: F401
from app.services.recommendation import build_recommendation, demand_skill, optimizer_skill  # noqa: F401

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
