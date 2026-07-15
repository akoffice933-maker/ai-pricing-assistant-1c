"""
AI Pricing Market MVP
=====================

Рабочий FastAPI-прототип новой архитектуры:

    Market Context -> Demand Curve -> Price Optimization -> 1C audit/action

Главный принцип:
    Мы НЕ прогнозируем цену напрямую.
    Мы прогнозируем спрос при разных ценах относительно рынка, затем оптимизируем цену
    под бизнес-цель и ограничения.

Запуск:
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000

Документация:
    http://localhost:8000/docs
"""

from __future__ import annotations

import math
import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

APP_VERSION = "2.0.0-market-mvp"
SERVICE_NAME = "AI Pricing Assistant — Market Demand MVP"
API_TOKEN = os.getenv("AI_PRICING_API_TOKEN")

app = FastAPI(
    title=SERVICE_NAME,
    version=APP_VERSION,
    description=(
        "Market-aware pricing: прогноз кривой спроса относительно рынка и оптимизация цены "
        "под цель бизнеса. LLM не считает цену — она вызывает эти навыки."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def verify_api_token(authorization: Optional[str] = Header(default=None)) -> None:
    if not API_TOKEN:
        return
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token",
        )


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    if denominator == 0:
        return default
    return numerator / denominator


class ItemType(str, Enum):
    PRODUCT = "product"
    SERVICE = "service"
    SUBSCRIPTION = "subscription"
    PROJECT = "project"


class PriceUnit(str, Enum):
    UNIT = "unit"
    HOUR = "hour"
    DAY = "day"
    PROJECT = "project"
    MONTH = "month"


class BusinessGoal(str, Enum):
    MAXIMIZE_PROFIT = "maximize_profit"
    MAXIMIZE_REVENUE = "maximize_revenue"
    GROW_MARKET_SHARE = "grow_market_share"
    CLEAR_STOCK = "clear_stock"
    PREMIUM_POSITIONING = "premium_positioning"
    MAXIMIZE_UTILIZATION = "maximize_utilization"


class ItemData(BaseModel):
    """Универсальная позиция: товар, услуга, проект или подписка."""

    model_config = ConfigDict(extra="forbid")

    item_id: str = Field(..., min_length=1)
    item_type: ItemType = ItemType.PRODUCT
    item_name: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)

    current_price: float = Field(..., gt=0, description="Текущая цена за единицу/час/проект")
    unit_cost: float = Field(0.0, ge=0, description="Полная переменная себестоимость единицы/часа/проекта")
    price_unit: PriceUnit = PriceUnit.UNIT
    currency: str = Field("EUR", min_length=1, max_length=8)

    sales_last_30_days: float = Field(0.0, ge=0, description="Факт продаж/сделок/часов за 30 дней")
    sales_last_90_days: float = Field(0.0, ge=0, description="Факт продаж/сделок/часов за 90 дней")

    stock_quantity: Optional[float] = Field(None, ge=0, description="Остаток для товаров")
    available_capacity: Optional[float] = Field(None, ge=0, description="Доступная мощность на горизонт: часы/слоты/единицы")
    team_utilization_percent: Optional[float] = Field(None, ge=0, le=100, description="Загрузка команды для услуг")

    target_margin_percent: float = Field(30.0, ge=0, le=95)
    quality_index: float = Field(1.0, ge=0.5, le=2.0, description="Относительная ценность: рейтинг, бренд, SLA, качество")
    conversion_rate_percent: Optional[float] = Field(None, ge=0, le=100)

    @model_validator(mode="after")
    def validate_service_fields(self) -> "ItemData":
        if self.item_type == ItemType.SERVICE and self.price_unit == PriceUnit.UNIT:
            # Не запрещаем: в 1С услуги часто лежат как номенклатура с ценой за единицу.
            pass
        return self


class MarketContext(BaseModel):
    """Индикаторы общего рынка для категории, региона и канала."""

    model_config = ConfigDict(extra="forbid")

    market_category: str = Field(..., min_length=1)
    region: str = Field("LV", min_length=1)
    channel: str = Field("online", min_length=1)
    period: Optional[str] = Field(None, description="Например 2026-07")

    market_price_min: Optional[float] = Field(None, gt=0)
    market_price_p25: Optional[float] = Field(None, gt=0)
    market_price_median: float = Field(..., gt=0)
    market_price_avg: Optional[float] = Field(None, gt=0)
    market_price_p75: Optional[float] = Field(None, gt=0)
    market_price_max: Optional[float] = Field(None, gt=0)

    competitor_count: int = Field(0, ge=0)
    active_competitor_count: Optional[int] = Field(None, ge=0)

    market_demand_index: float = Field(1.0, ge=0.05, le=5.0)
    search_trend_index: Optional[float] = Field(None, ge=0.05, le=5.0)
    lead_volume_index: Optional[float] = Field(None, ge=0.05, le=5.0)
    category_views_index: Optional[float] = Field(None, ge=0.05, le=5.0)

    promo_share: float = Field(0.0, ge=0, le=1, description="Доля конкурентов/рынка в промо")
    average_discount_percent: Optional[float] = Field(None, ge=0, le=100)
    availability_index: float = Field(1.0, ge=0, le=1, description="Доля рынка в наличии/доступности")
    stockout_rate: Optional[float] = Field(None, ge=0, le=1)
    average_delivery_days: Optional[float] = Field(None, ge=0)
    seasonality_index: float = Field(1.0, ge=0.05, le=5.0)

    # Для услуг/B2B
    tender_count: Optional[int] = Field(None, ge=0)
    conversion_benchmark: Optional[float] = Field(None, ge=0, le=1)
    specialist_supply_index: Optional[float] = Field(None, ge=0.05, le=5.0)
    wage_index: Optional[float] = Field(None, ge=0.05, le=5.0)

    data_freshness_days: int = Field(0, ge=0)
    source_count: Optional[int] = Field(None, ge=0)
    coverage_score: float = Field(1.0, ge=0, le=1)
    confidence: float = Field(0.8, ge=0, le=1)

    @field_validator("market_price_max")
    @classmethod
    def validate_price_max(cls, value: Optional[float], info: Any) -> Optional[float]:
        return value


class PricingConstraints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_margin_percent: float = Field(10.0, ge=0, le=95)
    max_price_increase_percent: float = Field(20.0, ge=0, le=500)
    max_price_decrease_percent: float = Field(30.0, ge=0, le=100)
    price_ending: Optional[float] = Field(0.99, ge=0, lt=1)
    min_confidence_for_apply: float = Field(0.70, ge=0, le=1)


class MarketObservation(BaseModel):
    """Сырое рыночное наблюдение: цена конкурента/оффера/ставки услуги."""

    model_config = ConfigDict(extra="forbid")

    price: float = Field(..., gt=0)
    competitor_id: Optional[str] = None
    source: str = Field("manual", min_length=1)
    is_promo: bool = False
    is_available: bool = True
    delivery_days: Optional[float] = Field(None, ge=0)
    data_freshness_days: int = Field(0, ge=0)


class MarketIndicatorsCalculationRequest(BaseModel):
    """Запрос на расчёт market_context из сырых наблюдений рынка."""

    model_config = ConfigDict(extra="forbid")

    market_category: str = Field(..., min_length=1)
    region: str = Field("LV", min_length=1)
    channel: str = Field("online", min_length=1)
    item_type: ItemType = ItemType.PRODUCT
    period: Optional[str] = None
    observations: List[MarketObservation] = Field(..., min_length=1)

    # Опциональные proxy-сигналы общего спроса. Если переданы, собираются в market_demand_index.
    search_trend_index: Optional[float] = Field(None, ge=0.05, le=5.0)
    lead_volume_index: Optional[float] = Field(None, ge=0.05, le=5.0)
    category_views_index: Optional[float] = Field(None, ge=0.05, le=5.0)
    seasonality_index: float = Field(1.0, ge=0.05, le=5.0)


class MarketIndicatorsCalculationResponse(BaseModel):
    market_context: MarketContext
    diagnostics: Dict[str, Any]
    calculation_timestamp: str


class DemandCurveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    item: ItemData
    market_context: MarketContext
    horizon_days: int = Field(30, ge=1, le=365)
    price_grid: Optional[List[float]] = Field(None, description="Если не передан, генерируется автоматически")
    elasticity_override: Optional[float] = Field(None, ge=-10, le=0)

    @field_validator("price_grid")
    @classmethod
    def validate_price_grid(cls, value: Optional[List[float]]) -> Optional[List[float]]:
        if value is None:
            return None
        clean = sorted({round(float(v), 2) for v in value if v > 0})
        if len(clean) < 2:
            raise ValueError("price_grid должен содержать минимум 2 положительные цены")
        return clean


class DemandPoint(BaseModel):
    price: float
    relative_price: float
    value_adjusted_relative_price: float
    expected_demand: float
    confidence: float
    expected_revenue: float
    expected_gross_profit: float
    margin_percent: float
    notes: List[str] = []


class DemandCurveResponse(BaseModel):
    request_id: str
    item_id: str
    item_type: str
    price_unit: str
    currency: str
    horizon_days: int
    market_demand_index: float
    elasticity: float
    current_relative_price: float
    demand_curve: List[DemandPoint]
    diagnostics: Dict[str, Any]
    calculation_timestamp: str


class PriceOptimizationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    business_goal: BusinessGoal = BusinessGoal.MAXIMIZE_PROFIT
    item: ItemData
    market_context: MarketContext
    demand_curve: List[DemandPoint]
    constraints: PricingConstraints = Field(default_factory=PricingConstraints)


class PriceOptimizationResponse(BaseModel):
    request_id: str
    item_id: str
    business_goal: str
    recommended_price: float
    current_price: float
    price_change_percent: float
    expected_demand: float
    expected_revenue: float
    expected_gross_profit: float
    expected_margin_percent: float
    confidence: float
    is_reliable: bool
    selected_point: DemandPoint
    rejected_points: List[Dict[str, Any]]
    constraints: Dict[str, Any]
    explanation: List[str]
    warnings: List[str]
    recommended_action: Dict[str, Any]
    calculation_timestamp: str


class PriceRecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    business_goal: BusinessGoal = BusinessGoal.MAXIMIZE_PROFIT
    item: ItemData
    market_context: MarketContext
    horizon_days: int = Field(30, ge=1, le=365)
    price_grid: Optional[List[float]] = None
    constraints: PricingConstraints = Field(default_factory=PricingConstraints)
    elasticity_override: Optional[float] = Field(None, ge=-10, le=0)


class PriceRecommendationResponse(BaseModel):
    request_id: str
    item_id: str
    item_name: str
    item_type: str
    market_category: str
    business_goal: str
    current_price: float
    recommended_price: float
    price_change_percent: float
    expected_demand: float
    expected_revenue: float
    expected_gross_profit: float
    expected_margin_percent: float
    confidence: float
    is_reliable: bool
    demand_curve: List[DemandPoint]
    elasticity: float
    market_context_summary: Dict[str, Any]
    explanation: Dict[str, List[str]]
    warnings: List[str]
    recommended_action: Dict[str, Any]
    model_version: str
    calculation_timestamp: str


def percentile(sorted_values: List[float], q: float) -> float:
    """Линейный percentile для уже отсортированного списка."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    pos = (len(sorted_values) - 1) * q
    low = math.floor(pos)
    high = math.ceil(pos)
    if low == high:
        return float(sorted_values[int(pos)])
    return float(sorted_values[low] * (high - pos) + sorted_values[high] * (pos - low))


def calculate_market_context_from_observations(
    request: MarketIndicatorsCalculationRequest,
) -> MarketIndicatorsCalculationResponse:
    prices = sorted([obs.price for obs in request.observations])
    count = len(prices)
    sources = {obs.source for obs in request.observations if obs.source}
    competitors = {obs.competitor_id for obs in request.observations if obs.competitor_id}

    promo_share = sum(1 for obs in request.observations if obs.is_promo) / count
    availability_index = sum(1 for obs in request.observations if obs.is_available) / count
    delivery_values = [obs.delivery_days for obs in request.observations if obs.delivery_days is not None]
    freshness = max(obs.data_freshness_days for obs in request.observations)

    demand_signal_values = [
        value
        for value in [
            request.search_trend_index,
            request.lead_volume_index,
            request.category_views_index,
        ]
        if value is not None
    ]
    if demand_signal_values:
        demand_signal_avg = sum(demand_signal_values) / len(demand_signal_values)
        market_demand_index = 0.75 * demand_signal_avg + 0.25 * request.seasonality_index
    else:
        market_demand_index = request.seasonality_index

    coverage_score = clamp(count / 15, 0.05, 1.0)
    freshness_penalty = 1.0
    if freshness > 30:
        freshness_penalty = 0.65
    elif freshness > 14:
        freshness_penalty = 0.82
    confidence = clamp((0.30 + 0.60 * coverage_score) * freshness_penalty, 0.05, 0.95)

    market_context = MarketContext(
        market_category=request.market_category,
        region=request.region,
        channel=request.channel,
        period=request.period,
        market_price_min=round(prices[0], 2),
        market_price_p25=round(percentile(prices, 0.25), 2),
        market_price_median=round(percentile(prices, 0.50), 2),
        market_price_avg=round(sum(prices) / count, 2),
        market_price_p75=round(percentile(prices, 0.75), 2),
        market_price_max=round(prices[-1], 2),
        competitor_count=len(competitors) if competitors else count,
        active_competitor_count=sum(1 for obs in request.observations if obs.is_available),
        market_demand_index=round(market_demand_index, 4),
        search_trend_index=request.search_trend_index,
        lead_volume_index=request.lead_volume_index,
        category_views_index=request.category_views_index,
        promo_share=round(promo_share, 4),
        availability_index=round(availability_index, 4),
        average_delivery_days=round(sum(delivery_values) / len(delivery_values), 2) if delivery_values else None,
        seasonality_index=request.seasonality_index,
        data_freshness_days=freshness,
        source_count=len(sources),
        coverage_score=round(coverage_score, 4),
        confidence=round(confidence, 4),
    )

    return MarketIndicatorsCalculationResponse(
        market_context=market_context,
        diagnostics={
            "observation_count": count,
            "unique_sources": len(sources),
            "unique_competitors": len(competitors),
            "formula": "market_demand_index = avg(search/lead/views)*0.75 + seasonality*0.25, fallback=seasonality",
            "confidence_rule": "confidence = (0.30 + 0.60*coverage_score) * freshness_penalty",
        },
        calculation_timestamp=now_iso(),
    )


# ============================================================
# Demand curve skill
# ============================================================


class DemandCurveSkill:
    version = "demand_curve_v1.0.0-market-relative"

    def forecast(self, request: DemandCurveRequest) -> DemandCurveResponse:
        item = request.item
        market = request.market_context
        price_grid = request.price_grid or self._auto_price_grid(item.current_price, market.market_price_median)

        elasticity = request.elasticity_override
        if elasticity is None:
            elasticity = self._estimate_elasticity(item, market)

        observed_demand = self._observed_demand_for_horizon(item, request.horizon_days)
        current_relative = item.current_price / market.market_price_median
        current_value_adjusted_relative = current_relative / item.quality_index

        market_multiplier = self._market_multiplier(market)
        competitive_multiplier = self._competitive_multiplier(market)

        current_price_response = self._price_response(current_value_adjusted_relative, elasticity)
        denominator = max(market_multiplier * competitive_multiplier * current_price_response, 1e-6)
        normalized_base_demand = observed_demand / denominator if observed_demand > 0 else self._fallback_base_demand(item, request.horizon_days)

        demand_curve: List[DemandPoint] = []
        for price in price_grid:
            relative_price = price / market.market_price_median
            value_adjusted_relative = relative_price / item.quality_index
            price_response = self._price_response(value_adjusted_relative, elasticity)
            demand = normalized_base_demand * market_multiplier * competitive_multiplier * price_response

            # Для услуг ограничиваем прогноз физической мощностью, если она передана.
            capacity_note = []
            if item.available_capacity is not None and demand > item.available_capacity:
                demand = item.available_capacity
                capacity_note.append("Спрос ограничен доступной мощностью/часами.")

            revenue = price * demand
            gross_profit = max(price - item.unit_cost, -10**12) * demand
            margin_percent = safe_div(price - item.unit_cost, price, 0.0) * 100
            confidence = self._point_confidence(item, market, price)

            notes = capacity_note + self._point_notes(item, market, price, relative_price)
            demand_curve.append(
                DemandPoint(
                    price=round(price, 2),
                    relative_price=round(relative_price, 4),
                    value_adjusted_relative_price=round(value_adjusted_relative, 4),
                    expected_demand=round(max(0.0, demand), 2),
                    confidence=round(confidence, 4),
                    expected_revenue=round(max(0.0, revenue), 2),
                    expected_gross_profit=round(gross_profit, 2),
                    margin_percent=round(margin_percent, 2),
                    notes=notes,
                )
            )

        diagnostics = {
            "observed_demand_for_horizon": round(observed_demand, 2),
            "normalized_base_demand": round(normalized_base_demand, 2),
            "market_multiplier": round(market_multiplier, 4),
            "competitive_multiplier": round(competitive_multiplier, 4),
            "current_price_response": round(current_price_response, 4),
            "formula": "Q(p)=base * market_multiplier * competitive_multiplier * (value_adjusted_relative_price ** elasticity)",
        }

        return DemandCurveResponse(
            request_id=request.request_id,
            item_id=item.item_id,
            item_type=item.item_type.value,
            price_unit=item.price_unit.value,
            currency=item.currency,
            horizon_days=request.horizon_days,
            market_demand_index=market.market_demand_index,
            elasticity=round(elasticity, 4),
            current_relative_price=round(current_relative, 4),
            demand_curve=demand_curve,
            diagnostics=diagnostics,
            calculation_timestamp=now_iso(),
        )

    def _auto_price_grid(self, current_price: float, market_median: float) -> List[float]:
        anchors = [current_price * factor for factor in [0.80, 0.90, 0.95, 1.00, 1.05, 1.10, 1.20]]
        anchors += [market_median * factor for factor in [0.90, 1.00, 1.10]]
        clean = sorted({round(max(0.01, value), 2) for value in anchors})
        return clean

    def _estimate_elasticity(self, item: ItemData, market: MarketContext) -> float:
        # Базовая эластичность: услуги обычно менее сравнимы, товары чаще более эластичны.
        if item.item_type == ItemType.PRODUCT:
            elasticity = -1.6
        elif item.item_type == ItemType.SERVICE:
            elasticity = -1.15
        elif item.item_type == ItemType.SUBSCRIPTION:
            elasticity = -1.30
        else:
            elasticity = -1.05

        # Больше конкурентов и промо — выше чувствительность к цене.
        elasticity *= 1 + min(market.competitor_count, 30) / 100
        elasticity *= 1 + 0.50 * market.promo_share

        # Качество/бренд/SLA снижает чувствительность к относительной цене.
        elasticity *= 1 - 0.25 * clamp(item.quality_index - 1.0, -0.5, 1.0)

        # Если рынок плохо доступен у конкурентов, цена менее критична.
        if market.availability_index < 0.75:
            elasticity *= 0.90

        return float(clamp(elasticity, -5.0, -0.2))

    def _observed_demand_for_horizon(self, item: ItemData, horizon_days: int) -> float:
        if item.sales_last_90_days > 0:
            daily = item.sales_last_90_days / 90
        elif item.sales_last_30_days > 0:
            daily = item.sales_last_30_days / 30
        else:
            daily = 0
        observed = daily * horizon_days
        # Если горизонт 30 дней и есть свежие 30-дневные данные, смешиваем 70/30.
        if horizon_days == 30 and item.sales_last_30_days > 0:
            observed = 0.70 * item.sales_last_30_days + 0.30 * observed
        return max(0.0, observed)

    def _fallback_base_demand(self, item: ItemData, horizon_days: int) -> float:
        if item.item_type == ItemType.SERVICE:
            return max(1.0, horizon_days / 7)
        return max(1.0, horizon_days / 3)

    def _market_multiplier(self, market: MarketContext) -> float:
        # market_demand_index — общий индекс спроса категории.
        # seasonality_index можно считать отдельным множителем, если он не включён в market_demand_index.
        return market.market_demand_index * market.seasonality_index

    def _competitive_multiplier(self, market: MarketContext) -> float:
        # Промо конкурентов снижает нашу долю спроса.
        promo_factor = 1 - 0.30 * market.promo_share
        # Если у конкурентов низкая доступность, часть спроса переходит к нам.
        availability_factor = 1 + 0.20 * (1 - market.availability_index)
        return clamp(promo_factor * availability_factor, 0.2, 1.5)

    def _price_response(self, value_adjusted_relative_price: float, elasticity: float) -> float:
        rel = max(value_adjusted_relative_price, 0.01)
        return rel ** elasticity

    def _point_confidence(self, item: ItemData, market: MarketContext, price: float) -> float:
        confidence = market.confidence * market.coverage_score
        if market.data_freshness_days > 30:
            confidence *= 0.75
        elif market.data_freshness_days > 14:
            confidence *= 0.88

        if item.sales_last_90_days < 20:
            confidence *= 0.70
        elif item.sales_last_90_days < 100:
            confidence *= 0.88

        distance_from_current = abs(math.log(price / item.current_price))
        confidence *= math.exp(-1.25 * distance_from_current)
        return clamp(confidence, 0.05, 0.99)

    def _point_notes(self, item: ItemData, market: MarketContext, price: float, relative_price: float) -> List[str]:
        notes: List[str] = []
        if relative_price > 1.10:
            notes.append("Цена выше медианы рынка более чем на 10%.")
        elif relative_price < 0.90:
            notes.append("Цена ниже медианы рынка более чем на 10%.")
        if market.promo_share > 0.40:
            notes.append("Высокая доля промо у конкурентов усиливает ценовое давление.")
        if market.data_freshness_days > 14:
            notes.append("Рыночные данные не самые свежие.")
        if item.unit_cost > 0 and price <= item.unit_cost:
            notes.append("Цена ниже или равна полной переменной себестоимости.")
        return notes


# ============================================================
# Price optimizer skill
# ============================================================


class PriceOptimizerSkill:
    version = "price_optimizer_v1.0.0"

    def optimize(self, request: PriceOptimizationRequest) -> PriceOptimizationResponse:
        item = request.item
        constraints = request.constraints
        feasible_points: List[DemandPoint] = []
        rejected_points: List[Dict[str, Any]] = []
        warnings: List[str] = []

        min_price_by_margin = self._min_price_by_margin(item.unit_cost, constraints.min_margin_percent)
        min_price_by_decrease = item.current_price * (1 - constraints.max_price_decrease_percent / 100)
        max_price_by_increase = item.current_price * (1 + constraints.max_price_increase_percent / 100)
        lower_bound = max(min_price_by_margin, min_price_by_decrease, 0.01)
        upper_bound = max_price_by_increase

        if lower_bound > upper_bound:
            warnings.append(
                "Минимальная цена по марже выше лимита повышения. "
                "Оптимизация требует ручного согласования."
            )
            upper_bound = lower_bound

        for point in request.demand_curve:
            reasons = []
            if point.price < lower_bound:
                reasons.append(f"ниже нижней границы {lower_bound:.2f}")
            if point.price > upper_bound:
                reasons.append(f"выше верхней границы {upper_bound:.2f}")
            if point.confidence < 0.05:
                reasons.append("слишком низкая надёжность")
            if reasons:
                rejected_points.append({"price": point.price, "reasons": reasons})
            else:
                feasible_points.append(point)

        if not feasible_points:
            # Берём ближайшую допустимую цену как fallback.
            warnings.append("Нет точек кривой, полностью удовлетворяющих ограничениям; выбран ближайший допустимый вариант.")
            selected = self._fallback_point(request.demand_curve, lower_bound, upper_bound)
        else:
            selected = self._select_by_goal(feasible_points, request.business_goal, item)

        rounded_price = self._round_price(selected.price, constraints.price_ending)
        if abs(rounded_price - selected.price) > 0.001:
            # После округления пересчитываем финансовые показатели приближённо на выбранном спросе.
            selected = selected.model_copy(
                update={
                    "price": rounded_price,
                    "expected_revenue": round(rounded_price * selected.expected_demand, 2),
                    "expected_gross_profit": round((rounded_price - item.unit_cost) * selected.expected_demand, 2),
                    "margin_percent": round(safe_div(rounded_price - item.unit_cost, rounded_price, 0) * 100, 2),
                }
            )

        is_reliable = selected.confidence >= constraints.min_confidence_for_apply
        explanation = self._explain_selection(request, selected, lower_bound, upper_bound)

        action_type = "create_price_change_draft" if is_reliable else "manual_review"
        if abs(selected.price / item.current_price - 1) * 100 > constraints.max_price_increase_percent:
            action_type = "manual_review"

        return PriceOptimizationResponse(
            request_id=request.request_id,
            item_id=item.item_id,
            business_goal=request.business_goal.value,
            recommended_price=round(selected.price, 2),
            current_price=round(item.current_price, 2),
            price_change_percent=round((selected.price / item.current_price - 1) * 100, 2),
            expected_demand=selected.expected_demand,
            expected_revenue=selected.expected_revenue,
            expected_gross_profit=selected.expected_gross_profit,
            expected_margin_percent=selected.margin_percent,
            confidence=selected.confidence,
            is_reliable=is_reliable,
            selected_point=selected,
            rejected_points=rejected_points,
            constraints={
                "min_price_by_margin": round(min_price_by_margin, 2),
                "min_price_by_decrease": round(min_price_by_decrease, 2),
                "max_price_by_increase": round(max_price_by_increase, 2),
                "lower_bound": round(lower_bound, 2),
                "upper_bound": round(upper_bound, 2),
            },
            explanation=explanation,
            warnings=warnings,
            recommended_action={
                "type": action_type,
                "requires_approval": True,
                "document_type": "УстановкаЦенНоменклатуры",
                "valid_for_days": 14 if is_reliable else 7,
                "priority": "high" if abs(selected.price / item.current_price - 1) > 0.05 else "normal",
            },
            calculation_timestamp=now_iso(),
        )

    def _min_price_by_margin(self, unit_cost: float, min_margin_percent: float) -> float:
        if unit_cost <= 0:
            return 0.01
        if min_margin_percent >= 95:
            min_margin_percent = 95
        return unit_cost / (1 - min_margin_percent / 100)

    def _select_by_goal(self, points: List[DemandPoint], goal: BusinessGoal, item: ItemData) -> DemandPoint:
        if goal == BusinessGoal.MAXIMIZE_PROFIT:
            return max(points, key=lambda p: (p.expected_gross_profit, p.confidence))
        if goal == BusinessGoal.MAXIMIZE_REVENUE:
            return max(points, key=lambda p: (p.expected_revenue, p.confidence))
        if goal == BusinessGoal.GROW_MARKET_SHARE:
            return max(points, key=lambda p: (p.expected_demand, p.confidence))
        if goal == BusinessGoal.CLEAR_STOCK:
            if item.stock_quantity is not None:
                target = min(item.stock_quantity, max(p.expected_demand for p in points))
                return min(points, key=lambda p: (abs(p.expected_demand - target), p.price))
            return max(points, key=lambda p: p.expected_demand)
        if goal == BusinessGoal.PREMIUM_POSITIONING:
            max_demand = max(p.expected_demand for p in points)
            acceptable = [p for p in points if p.expected_demand >= max_demand * 0.55]
            return max(acceptable or points, key=lambda p: (p.price, p.margin_percent))
        if goal == BusinessGoal.MAXIMIZE_UTILIZATION:
            if item.available_capacity:
                target_demand = item.available_capacity * 0.85
                return min(points, key=lambda p: (abs(p.expected_demand - target_demand), -p.expected_gross_profit))
            return max(points, key=lambda p: p.expected_demand)
        return max(points, key=lambda p: p.expected_gross_profit)

    def _fallback_point(self, points: List[DemandPoint], lower_bound: float, upper_bound: float) -> DemandPoint:
        return min(points, key=lambda p: min(abs(p.price - lower_bound), abs(p.price - upper_bound)))

    def _round_price(self, price: float, ending: Optional[float]) -> float:
        if ending is None:
            return round(price, 2)
        if ending <= 0 or ending >= 1:
            return round(price, 2)
        return round(math.floor(price) + ending, 2)

    def _explain_selection(
        self,
        request: PriceOptimizationRequest,
        selected: DemandPoint,
        lower_bound: float,
        upper_bound: float,
    ) -> List[str]:
        item = request.item
        explanation = [
            f"Выбрана цена {selected.price:.2f} {item.currency} под цель {request.business_goal.value}.",
            f"При этой цене ожидаемый спрос за период: {selected.expected_demand:.2f}, выручка: {selected.expected_revenue:.2f}, валовая прибыль: {selected.expected_gross_profit:.2f}.",
            f"Цена находится в допустимом диапазоне {lower_bound:.2f}–{upper_bound:.2f} с учётом маржи и лимитов изменения.",
        ]
        if selected.relative_price > 1.05:
            explanation.append(f"Цена выше медианы рынка на {(selected.relative_price - 1) * 100:.1f}%.")
        elif selected.relative_price < 0.95:
            explanation.append(f"Цена ниже медианы рынка на {(1 - selected.relative_price) * 100:.1f}%.")
        else:
            explanation.append("Цена находится около медианы рынка.")
        return explanation


# ============================================================
# Recommendation orchestrator
# ============================================================


demand_skill = DemandCurveSkill()
optimizer_skill = PriceOptimizerSkill()


def build_recommendation(request: PriceRecommendationRequest) -> PriceRecommendationResponse:
    curve_request = DemandCurveRequest(
        request_id=request.request_id,
        user_id=request.user_id,
        item=request.item,
        market_context=request.market_context,
        horizon_days=request.horizon_days,
        price_grid=request.price_grid,
        elasticity_override=request.elasticity_override,
    )
    curve_response = demand_skill.forecast(curve_request)

    optimization_request = PriceOptimizationRequest(
        request_id=request.request_id,
        user_id=request.user_id,
        business_goal=request.business_goal,
        item=request.item,
        market_context=request.market_context,
        demand_curve=curve_response.demand_curve,
        constraints=request.constraints,
    )
    optimization = optimizer_skill.optimize(optimization_request)

    positive: List[str] = []
    negative: List[str] = []
    neutral: List[str] = []

    market = request.market_context
    item = request.item
    if market.market_demand_index > 1.10:
        positive.append(f"Общий рыночный спрос выше нормы: индекс {market.market_demand_index:.2f}.")
    elif market.market_demand_index < 0.90:
        negative.append(f"Общий рыночный спрос ниже нормы: индекс {market.market_demand_index:.2f}.")
    else:
        neutral.append("Общий рыночный спрос около нормы.")

    if market.promo_share > 0.30:
        negative.append(f"Высокое промо-давление конкурентов: {market.promo_share:.0%} рынка в промо.")

    current_relative = item.current_price / market.market_price_median
    recommended_relative = optimization.recommended_price / market.market_price_median
    neutral.append(f"Текущая цена относительно медианы рынка: {current_relative:.3f}.")
    neutral.append(f"Рекомендованная цена относительно медианы рынка: {recommended_relative:.3f}.")

    if item.quality_index > 1.05:
        positive.append(f"Позиция имеет премию ценности/качества: индекс {item.quality_index:.2f}.")
    elif item.quality_index < 0.95:
        negative.append(f"Индекс ценности ниже среднего: {item.quality_index:.2f}.")

    if not positive:
        positive.append("Позитивные рыночные драйверы выражены умеренно.")
    if not negative:
        neutral.append("Критичных негативных факторов не выявлено.")

    return PriceRecommendationResponse(
        request_id=request.request_id,
        item_id=item.item_id,
        item_name=item.item_name,
        item_type=item.item_type.value,
        market_category=market.market_category,
        business_goal=request.business_goal.value,
        current_price=optimization.current_price,
        recommended_price=optimization.recommended_price,
        price_change_percent=optimization.price_change_percent,
        expected_demand=optimization.expected_demand,
        expected_revenue=optimization.expected_revenue,
        expected_gross_profit=optimization.expected_gross_profit,
        expected_margin_percent=optimization.expected_margin_percent,
        confidence=optimization.confidence,
        is_reliable=optimization.is_reliable,
        demand_curve=curve_response.demand_curve,
        elasticity=curve_response.elasticity,
        market_context_summary={
            "market_price_median": market.market_price_median,
            "market_demand_index": market.market_demand_index,
            "promo_share": market.promo_share,
            "availability_index": market.availability_index,
            "seasonality_index": market.seasonality_index,
            "data_freshness_days": market.data_freshness_days,
            "confidence": market.confidence,
        },
        explanation={
            "summary": optimization.explanation,
            "positive_factors": positive,
            "negative_factors": negative,
            "neutral_factors": neutral,
        },
        warnings=optimization.warnings,
        recommended_action=optimization.recommended_action,
        model_version=f"{demand_skill.version}+{optimizer_skill.version}",
        calculation_timestamp=now_iso(),
    )


# ============================================================
# API
# ============================================================


@app.get("/")
async def root() -> Dict[str, Any]:
    return {
        "service": SERVICE_NAME,
        "version": APP_VERSION,
        "principle": "Market Context -> Demand Curve -> Price Optimization. LLM orchestrates, skills calculate.",
        "endpoints": [
            "POST /skills/forecast_demand_curve",
            "POST /skills/optimize_price",
            "POST /skills/recommend_price",
        ],
        "docs": "/docs",
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok", "service": SERVICE_NAME, "version": APP_VERSION, "timestamp": now_iso()}


@app.get("/model_info")
async def model_info(_: None = Depends(verify_api_token)) -> Dict[str, Any]:
    return {
        "version": APP_VERSION,
        "skills": {
            "forecast_demand_curve": demand_skill.version,
            "optimize_price": optimizer_skill.version,
            "recommend_price": "orchestrator",
        },
        "core_formula": "Q(p)=base * market_multiplier * competitive_multiplier * (value_adjusted_relative_price ** elasticity)",
        "note": "MVP uses calibrated elasticity model. Production should train elasticity/demand models on history + market indicators.",
    }


@app.post("/market/calculate_indicators", response_model=MarketIndicatorsCalculationResponse)
async def calculate_market_indicators(
    request: MarketIndicatorsCalculationRequest,
    _: None = Depends(verify_api_token),
) -> MarketIndicatorsCalculationResponse:
    """
    Рассчитывает market_context из сырых рыночных наблюдений.

    Этот endpoint нужен для Stage 3 / real market data: парсер конкурентов или CRM
    может отправить набор наблюдений, а сервис вернёт нормализованные индикаторы
    для регистра 1С `AI_РыночныеИндикаторы`.
    """
    return calculate_market_context_from_observations(request)


@app.post("/skills/forecast_demand_curve", response_model=DemandCurveResponse)
async def forecast_demand_curve(
    request: DemandCurveRequest,
    _: None = Depends(verify_api_token),
) -> DemandCurveResponse:
    return demand_skill.forecast(request)


@app.post("/skills/optimize_price", response_model=PriceOptimizationResponse)
async def optimize_price(
    request: PriceOptimizationRequest,
    _: None = Depends(verify_api_token),
) -> PriceOptimizationResponse:
    return optimizer_skill.optimize(request)


@app.post("/skills/recommend_price", response_model=PriceRecommendationResponse)
async def recommend_price(
    request: PriceRecommendationRequest,
    _: None = Depends(verify_api_token),
) -> PriceRecommendationResponse:
    return build_recommendation(request)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
