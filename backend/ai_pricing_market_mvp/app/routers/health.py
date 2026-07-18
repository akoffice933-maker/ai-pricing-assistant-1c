"""Служебные эндпоинты: корень, liveness, readiness, инфо о модели."""

from typing import Any, Dict

from fastapi import APIRouter, Depends

from app import config
from app.config import APP_VERSION, SERVICE_NAME
from app.security import verify_api_token
from app.services.recommendation import demand_skill, optimizer_skill
from app.utils import now_iso

router = APIRouter()


@router.get("/")
async def root() -> Dict[str, Any]:
    return {
        "service": SERVICE_NAME,
        "version": APP_VERSION,
        "principle": "Market Context -> Demand Curve -> Price Optimization. LLM orchestrates, skills calculate.",
        "endpoints": [
            "POST /skills/forecast_demand_curve",
            "POST /skills/optimize_price",
            "POST /skills/recommend_price",
            "POST /skills/recommend_price/batch",
            "POST /market/calculate_indicators",
            "POST /market/calculate_indicators/export_1c",
            "(тот же набор доступен и с префиксом /v1)",
        ],
        "docs": "/docs",
    }


@router.get("/health")
async def health() -> Dict[str, Any]:
    """Liveness — процесс жив. Не проверяет внешние зависимости (их пока нет)."""
    return {"status": "ok", "service": SERVICE_NAME, "version": APP_VERSION, "timestamp": now_iso()}


@router.get("/ready")
async def ready() -> Dict[str, Any]:
    """Readiness — сервис сконфигурирован и готов принимать трафик."""
    invalid_origins = [o for o in config.ALLOWED_ORIGINS if not config._origin_looks_valid(o)]
    checks = {
        "auth_configured": bool(config.API_TOKEN) or not config.IS_PRODUCTION,
        "cors_configured": bool(config.ALLOWED_ORIGINS) or not config.IS_PRODUCTION,
        "cors_origins_look_valid": not invalid_origins,
    }
    ok = all(checks.values())
    return {
        "status": "ok" if ok else "degraded",
        "checks": checks,
        "allowed_origins": config.ALLOWED_ORIGINS,
        "timestamp": now_iso(),
    }


@router.get("/model_info")
async def model_info(_: None = Depends(verify_api_token)) -> Dict[str, Any]:
    return {
        "version": APP_VERSION,
        "skills": {
            "forecast_demand_curve": demand_skill.version,
            "optimize_price": optimizer_skill.version,
            "recommend_price": "orchestrator",
        },
        "core_formula": "Q(p)=base * forecast_market_multiplier * forecast_competitive_multiplier * (value_adjusted_relative_price ** elasticity)",
        "note": (
            "Эластичность — калиброванная эвристика, НЕ обучена и не провалидирована на реальных "
            "парах цена/спрос. market_demand_index без внешнего источника данных вырождается в "
            "seasonality_index. Рекомендации — подсказка для человека, не источник истины; "
            "автоматическое применение цены не предусмотрено."
        ),
    }
