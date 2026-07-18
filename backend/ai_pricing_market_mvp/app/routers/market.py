"""Эндпоинты расчёта рыночных индикаторов."""

from typing import Any, Dict, List

from fastapi import APIRouter, Body, Depends, Request

from app.rate_limit import _rate_limit
from app.config import RATE_LIMIT
from app.schemas import MarketIndicatorsCalculationRequest, MarketIndicatorsCalculationResponse
from app.security import verify_api_token
from app.services.market_indicators import calculate_market_context_from_observations

router = APIRouter(prefix="/market", tags=["market"])


@router.post("/calculate_indicators", response_model=MarketIndicatorsCalculationResponse)
@_rate_limit(RATE_LIMIT)
async def calculate_market_indicators(
    request: Request,
    body: MarketIndicatorsCalculationRequest = Body(...),
    _: None = Depends(verify_api_token),
) -> MarketIndicatorsCalculationResponse:
    """
    Рассчитывает market_context из сырых рыночных наблюдений.

    Этот endpoint нужен для Stage 3 / real market data: парсер конкурентов или CRM
    может отправить набор наблюдений, а сервис вернёт нормализованные индикаторы
    для регистра 1С `AI_РыночныеИндикаторы`.
    """
    return calculate_market_context_from_observations(body)


@router.post("/calculate_indicators/export_1c", response_model=List[Dict[str, Any]])
@_rate_limit(RATE_LIMIT)
async def calculate_market_indicators_export_1c(
    request: Request,
    body: MarketIndicatorsCalculationRequest = Body(...),
    _: None = Depends(verify_api_token),
) -> List[Dict[str, Any]]:
    """Возвращает массив записей, совместимый с 1С loader `AI_РыночныеИндикаторы`."""
    result = calculate_market_context_from_observations(body)
    return [result.one_c_indicator_record]
