"""
AI Pricing Market MVP
==============
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

import logging
import math
import os
import secrets
import sys
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address

    _SLOWAPI_AVAILABLE = True
except ImportError:  # pragma: no cover - slowapi is an optional prod dependency
    _SLOWAPI_AVAILABLE = False

APP_VERSION = "2.1.0-production"
SERVICE_NAME = "AI Pricing Assistant — Market Demand MVP"

# ============================================================
# Configuration (env-driven; see .env.example)
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
# Logging
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

# ============================================================
# App + middleware
# ============================================================
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
    allow_origins=ALLOWED_ORIGINS or [],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

if _SLOWAPI_AVAILABLE:
    limiter = Limiter(key_func=get_remote_address, default_limits=[RATE_LIMIT])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
elif IS_PRODUCTION:
    # slowapi зафиксирован в requirements.txt как обязательная зависимость — если его нет
    # в production, это признак сломанной установки, а не осознанного выбора. Как и с
    # токеном, лучше не стартовать вообще, чем молча остаться без rate limiting.
    raise RuntimeError(
        "slowapi не установлен, а ENVIRONMENT=production. Rate limiting обязателен в проде — "
        "проверьте, что requirements.txt установлен полностью (pip install -r requirements.txt)."
    )
else:  # pragma: no cover
    logger.warning(
        "slowapi не установлен — rate limiting отключён (допустимо только вне production). "
        "Добавьте slowapi в requirements.txt для production."
    )


@app.middleware("http")
async def request_context_middleware(request: Request, call_next: Callable) -> Response:
    """Присваивает request_id, логирует каждый запрос и время выполнения."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start = time.perf_counter()
    response: Optional[Response] = None
    try:
        response = await call_next(request)
        return response
    finally:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        status_code = response.status_code if response is not None else 500
        logger.info(
            "%s %s status=%s duration_ms=%s request_id=%s",
            request.method,
            request.url.path,
            status_code,
            duration_ms,
            request_id,
        )
        if response is not None:
            response.headers["X-Request-ID"] = request_id


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    safe_errors = jsonable_encoder(exc.errors(), exclude={"ctx"})
    logger.warning("validation_error path=%s errors=%s", request.url.path, safe_errors)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Некорректные входные данные", "errors": safe_errors},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Не отдаём наружу стектрейс/детали исключения — только в лог сервера.
    logger.exception("unhandled_error path=%s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Внутренняя ошибка сервера"},
    )


async def verify_api_token(authorization: Optional[str] = Header(default=None)) -> None:
    if not API_TOKEN:
        # Разрешено только вне production (см. проверку при старте выше).
        return
    expected = f"Bearer {API_TOKEN}"
    if not authorization or not secrets.compare_digest(authorization, expected):
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

    @model_validator(mode="after")
    def validate_price_percentiles_order(self) -> "MarketContext":
        """Проверяет согласованность рыночных перцентилей цены, если они заданы."""
        ordered = [
            ("market_price_min", self.market_price_min),
            ("market_price_p25", self.market_price_p25),
            ("market_price_median", self.market_price_median),
            ("market_price_p75", self.market_price_p75),
            ("market_price_max", self.market_price_max),
        ]
        present = [(name, value) for name, value in ordered if value is not None]
        for (name_a, value_a), (name_b, value_b) in zip(present, present[1:]):
            if value_a > value_b:
                raise ValueError(
                    f"Рыночные перцентили цены несогласованы: {name_a}={value_a} > {name_b}={value_b}"
                )
        return self


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
    one_c_indicator_record: Dict[str, Any]
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

    # Baseline-индексы описывают рынок периода, из которого взяты sales_last_30/90.
    # Forecast market_context описывает будущий/текущий рынок для рекомендации.
    # Это не даёт market_demand_index сократиться при калибровке по истории продаж.
    baseline_market_price_median: Optional[float] = Field(None, gt=0)
    baseline_market_demand_index: float = Field(1.0, ge=0.05, le=5.0)
    baseline_promo_share: float = Field(0.0, ge=0, le=1)
    baseline_availability_index: float = Field(1.0, ge=0, le=1)

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
    demand_curve: List[DemandPoint] = Field(..., min_length=1)
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
    baseline_market_price_median: Optional[float] = Field(None, gt=0)
    baseline_market_demand_index: float = Field(1.0, ge=0.05, le=5.0)
    baseline_promo_share: float = Field(0.0, ge=0, le=1)
    baseline_availability_index: float = Field(1.0, ge=0, le=1)


class PriceRecommendationResponse(BaseModel):
    request_id: str
    item_id: str
    item_name: str
    item_type: str
    price_unit: str
    currency: str
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
    price_bounds: Dict[str, float]
    rejected_points: List[Dict[str, Any]]
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

    one_c_indicator_record = market_context.model_dump(exclude_none=True)
    one_c_indicator_record.update(
        {
            "item_type": request.item_type.value,
            "source": "calculated_api",
            "currency": "EUR",
            "calculation_method": "POST /market/calculate_indicators",
        }
    )

    return MarketIndicatorsCalculationResponse(
        market_context=market_context,
        one_c_indicator_record=one_c_indicator_record,
        diagnostics={
            "observation_count": count,
            "unique_sources": len(sources),
            "unique_competitors": len(competitors),
            "formula": "market_demand_index = avg(search/lead/views)*0.75 + seasonality*0.25, fallback=seasonality",
            "confidence_rule": "confidence = (0.30 + 0.60*coverage_score) * freshness_penalty",
            "note": "market_demand_index already includes seasonality in this MVP calculator",
        },
        calculation_timestamp=now_iso(),
    )


# =====================================================# Demand curve skill
# =====================================================

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

        # Baseline describes the period behind sales_last_30/90; forecast market describes
        # the period for which we recommend the price. If baseline is not provided,
        # we assume a normal market (1.0). This keeps market_demand_index meaningful.
        baseline_market_price = request.baseline_market_price_median or market.market_price_median
        baseline_relative = item.current_price / baseline_market_price
        baseline_value_adjusted_relative = baseline_relative / item.quality_index

        forecast_market_multiplier = self._market_multiplier(market)
        forecast_competitive_multiplier = self._competitive_multiplier(market)
        baseline_market_multiplier = request.baseline_market_demand_index
        baseline_competitive_multiplier = self._competitive_multiplier_from_values(
            request.baseline_promo_share,
            request.baseline_availability_index,
        )

        baseline_price_response = self._price_response(baseline_value_adjusted_relative, elasticity)
        denominator = max(baseline_market_multiplier * baseline_competitive_multiplier * baseline_price_response, 1e-6)
        normalized_base_demand = observed_demand / denominator if observed_demand > 0 else self._fallback_base_demand(item, request.horizon_days)

        demand_curve: List[DemandPoint] = []
        for price in price_grid:
            relative_price = price / market.market_price_median
            value_adjusted_relative = relative_price / item.quality_index
            price_response = self._price_response(value_adjusted_relative, elasticity)
            demand = normalized_base_demand * forecast_market_multiplier * forecast_competitive_multiplier * price_response

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
            "baseline_market_multiplier": round(baseline_market_multiplier, 4),
            "baseline_competitive_multiplier": round(baseline_competitive_multiplier, 4),
            "baseline_price_response": round(baseline_price_response, 4),
            "forecast_market_multiplier": round(forecast_market_multiplier, 4),
            "forecast_competitive_multiplier": round(forecast_competitive_multiplier, 4),
            "formula": "Q(p)=base * forecast_market_multiplier * forecast_competitive_multiplier * (value_adjusted_relative_price ** elasticity)",
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
        # В MVP market_demand_index уже считается итоговым индексом общего спроса.
        # seasonality_index хранится отдельно для объяснения и расчёта market_demand_index,
        # но здесь не умножается повторно, чтобы не было двойного учёта сезонности.
        return market.market_demand_index

    def _competitive_multiplier(self, market: MarketContext) -> float:
        return self._competitive_multiplier_from_values(market.promo_share, market.availability_index)

    def _competitive_multiplier_from_values(self, promo_share: float, availability_index: float) -> float:
        # Промо конкурентов снижает нашу долю спроса.
        promo_factor = 1 - 0.30 * promo_share
        # Если у конкурентов низкая доступность, часть спроса переходит к нам.
        availability_factor = 1 + 0.20 * (1 - availability_index)
        return clamp(promo_factor * availability_factor, 0.2, 1.5)

    def _price_response(self, value_adjusted_relative_price: float, elasticity: float) -> float:
        rel = max(value_adjusted_relative_price, 0.01)
        return rel ** elasticity

    def _point_confidence(self, item: ItemData, market: MarketContext, price: float) -> float:
        # market.confidence should already include source coverage and data freshness.
        # Do not multiply coverage/freshness twice here; only add model-specific penalties.
        confidence = market.confidence

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


# =====================================================# Price optimizer skill
# =====================================================

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
            # Берём ближайшую точку кривой и принудительно приводим цену к допустимой границе.
            warnings.append("Нет точек кривой, полностью удовлетворяющих ограничениям; выбран ближайший допустимый вариант.")
            selected = self._fallback_point(request.demand_curve, lower_bound, upper_bound, item)
        else:
            selected = self._select_by_goal(feasible_points, request.business_goal, item)

        rounded_price = self._round_price(selected.price, constraints.price_ending)
        bounded_price = clamp(rounded_price, lower_bound, upper_bound)
        if abs(bounded_price - rounded_price) > 0.001:
            warnings.append("Цена после округления была скорректирована до допустимой границы.")
        if abs(bounded_price - selected.price) > 0.001:
            # После округления и clamp пересчитываем финансовые показатели приближённо на выбранном спросе.
            selected = self._with_price(selected, bounded_price, item)

        target_demand = self._goal_target_demand(request.business_goal, item, request.demand_curve)
        if target_demand is not None and target_demand <= 0:
            warnings.append(
                "Остаток/доступная мощность равны нулю — цель бизнес-цели вырождена (продавать нечего). "
                "Рекомендация не отражает содержательную оптимизацию; требуется ручной пересмотр "
                "остатка/мощности, а не автоматическое применение цены."
            )
        elif target_demand is not None and target_demand > 0:
            deviation = abs(selected.expected_demand - target_demand) / target_demand
            if deviation > 0.25:
                warnings.append(
                    f"Целевой спрос по бизнес-цели ({target_demand:.1f}) недостижим в рамках текущих "
                    f"ограничений цены; фактический прогнозный спрос при рекомендованной цене — "
                    f"{selected.expected_demand:.1f}. Рассмотрите смягчение max_price_increase_percent / "
                    f"max_price_decrease_percent, либо ручной пересмотр остатка/мощности."
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

    def _goal_target_demand(
        self, goal: BusinessGoal, item: ItemData, points: List[DemandPoint]
    ) -> Optional[float]:
        """Целевой спрос, которого пытается достичь бизнес-цель (если применимо)."""
        if goal == BusinessGoal.CLEAR_STOCK and item.stock_quantity is not None:
            return min(item.stock_quantity, max(p.expected_demand for p in points))
        if goal == BusinessGoal.MAXIMIZE_UTILIZATION and item.available_capacity is not None:
            return item.available_capacity * 0.85
        return None

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
            if item.available_capacity is not None:
                target_demand = item.available_capacity * 0.85
                return min(points, key=lambda p: (abs(p.expected_demand - target_demand), -p.expected_gross_profit))
            return max(points, key=lambda p: p.expected_demand)
        return max(points, key=lambda p: p.expected_gross_profit)

    def _fallback_point(self, points: List[DemandPoint], lower_bound: float, upper_bound: float, item: ItemData) -> DemandPoint:
        nearest = min(points, key=lambda p: min(abs(p.price - lower_bound), abs(p.price - upper_bound)))
        bounded_price = clamp(nearest.price, lower_bound, upper_bound)
        return self._with_price(nearest, bounded_price, item)

    def _with_price(self, point: DemandPoint, price: float, item: ItemData) -> DemandPoint:
        return point.model_copy(
            update={
                "price": round(price, 2),
                "expected_revenue": round(price * point.expected_demand, 2),
                "expected_gross_profit": round((price - item.unit_cost) * point.expected_demand, 2),
                "margin_percent": round(safe_div(price - item.unit_cost, price, 0) * 100, 2),
            }
        )

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


# =====================================================# Recommendation orchestrator
# =====================================================

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
        baseline_market_price_median=request.baseline_market_price_median,
        baseline_market_demand_index=request.baseline_market_demand_index,
        baseline_promo_share=request.baseline_promo_share,
        baseline_availability_index=request.baseline_availability_index,
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
        price_unit=item.price_unit.value,
        currency=item.currency,
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
        market_context_summary=market.model_dump(exclude_none=True),
        explanation={
            "summary": optimization.explanation,
            "positive_factors": positive,
            "negative_factors": negative,
            "neutral_factors": neutral,
        },
        warnings=optimization.warnings,
        recommended_action=optimization.recommended_action,
        price_bounds={
            "lower_bound": optimization.constraints["lower_bound"],
            "upper_bound": optimization.constraints["upper_bound"],
        },
        rejected_points=optimization.rejected_points,
        model_version=f"{demand_skill.version}+{optimizer_skill.version}",
        calculation_timestamp=now_iso(),
    )


# =====================================================# API
# =====================================================

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
            "POST /market/calculate_indicators",
            "POST /market/calculate_indicators/export_1c",
        ],
        "docs": "/docs",
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Liveness — процесс жив. Не проверяет внешние зависимости (их пока нет)."""
    return {"status": "ok", "service": SERVICE_NAME, "version": APP_VERSION, "timestamp": now_iso()}


@app.get("/ready")
async def ready() -> Dict[str, Any]:
    """Readiness — сервис сконфигурирован и готов принимать трафик."""
    invalid_origins = [o for o in ALLOWED_ORIGINS if not _origin_looks_valid(o)]
    checks = {
        "auth_configured": bool(API_TOKEN) or not IS_PRODUCTION,
        "cors_configured": bool(ALLOWED_ORIGINS) or not IS_PRODUCTION,
        "cors_origins_look_valid": not invalid_origins,
    }
    ok = all(checks.values())
    return {
        "status": "ok" if ok else "degraded",
        "checks": checks,
        "allowed_origins": ALLOWED_ORIGINS,
        "timestamp": now_iso(),
    }


@app.get("/model_info")
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


def _rate_limit(spec: str) -> Callable:
    """No-op decorator when slowapi isn't installed, so routes stay importable."""
    if _SLOWAPI_AVAILABLE:
        return limiter.limit(spec)
    return lambda func: func


@app.post("/market/calculate_indicators", response_model=MarketIndicatorsCalculationResponse)
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


@app.post("/market/calculate_indicators/export_1c", response_model=List[Dict[str, Any]])
@_rate_limit(RATE_LIMIT)
async def calculate_market_indicators_export_1c(
    request: Request,
    body: MarketIndicatorsCalculationRequest = Body(...),
    _: None = Depends(verify_api_token),
) -> List[Dict[str, Any]]:
    """Возвращает массив записей, совместимый с 1С loader `AI_РыночныеИндикаторы`."""
    result = calculate_market_context_from_observations(body)
    return [result.one_c_indicator_record]


@app.post("/skills/forecast_demand_curve", response_model=DemandCurveResponse)
@_rate_limit(RATE_LIMIT)
async def forecast_demand_curve(
    request: Request,
    body: DemandCurveRequest = Body(...),
    _: None = Depends(verify_api_token),
) -> DemandCurveResponse:
    return demand_skill.forecast(body)


@app.post("/skills/optimize_price", response_model=PriceOptimizationResponse)
@_rate_limit(RATE_LIMIT)
async def optimize_price(
    request: Request,
    body: PriceOptimizationRequest = Body(...),
    _: None = Depends(verify_api_token),
) -> PriceOptimizationResponse:
    return optimizer_skill.optimize(body)


@app.post("/skills/recommend_price", response_model=PriceRecommendationResponse)
@_rate_limit(RATE_LIMIT)
async def recommend_price(
    request: Request,
    body: PriceRecommendationRequest = Body(...),
    _: None = Depends(verify_api_token),
) -> PriceRecommendationResponse:
    return build_recommendation(body)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
