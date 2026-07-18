"""Эндпоинты расчётных skills: кривая спроса, оптимизация, рекомендация (+ batch)."""

from fastapi import APIRouter, Body, Depends, Request

from app.rate_limit import _rate_limit
from app.config import RATE_LIMIT
from app.schemas import (
    BatchPriceRecommendationRequest,
    BatchPriceRecommendationResponse,
    DemandCurveRequest,
    DemandCurveResponse,
    PriceOptimizationRequest,
    PriceOptimizationResponse,
    PriceRecommendationRequest,
    PriceRecommendationResponse,
)
from app.security import verify_api_token
from app.services.recommendation import build_batch_recommendations, build_recommendation, demand_skill, optimizer_skill

router = APIRouter(prefix="/skills", tags=["skills"])


@router.post("/forecast_demand_curve", response_model=DemandCurveResponse)
@_rate_limit(RATE_LIMIT)
async def forecast_demand_curve(
    request: Request,
    body: DemandCurveRequest = Body(...),
    _: None = Depends(verify_api_token),
) -> DemandCurveResponse:
    return demand_skill.forecast(body)


@router.post("/optimize_price", response_model=PriceOptimizationResponse)
@_rate_limit(RATE_LIMIT)
async def optimize_price(
    request: Request,
    body: PriceOptimizationRequest = Body(...),
    _: None = Depends(verify_api_token),
) -> PriceOptimizationResponse:
    return optimizer_skill.optimize(body)


@router.post("/recommend_price", response_model=PriceRecommendationResponse)
@_rate_limit(RATE_LIMIT)
async def recommend_price(
    request: Request,
    body: PriceRecommendationRequest = Body(...),
    _: None = Depends(verify_api_token),
) -> PriceRecommendationResponse:
    return build_recommendation(body)


@router.post("/recommend_price/batch", response_model=BatchPriceRecommendationResponse)
@_rate_limit("10/minute")
async def recommend_price_batch(
    request: Request,
    body: BatchPriceRecommendationRequest = Body(...),
    _: None = Depends(verify_api_token),
) -> BatchPriceRecommendationResponse:
    """Массовый расчёт (до 200 позиций). Отдельный, более строгий rate limit —

    один вызов здесь эквивалентен по нагрузке десяткам/сотням вызовов recommend_price.
    Некорректные позиции не роняют весь пакет — см. build_batch_recommendations.
    """
    return build_batch_recommendations(body)
