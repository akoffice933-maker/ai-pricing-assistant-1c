"""Pydantic-схемы: перечисления, входные/выходные модели API.

Скопировано без изменений логики из исходного монолитного main.py — см. git history
при необходимости сверить построчно.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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

    request_id: str = Field(default_factory=lambda: str(uuid4()))
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

    request_id: str = Field(default_factory=lambda: str(uuid4()))
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

    request_id: str = Field(default_factory=lambda: str(uuid4()))
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


class BatchPriceRecommendationRequest(BaseModel):
    """Пакетный расчёт рекомендаций — до 200 позиций за один вызов.

    Каждый элемент items — произвольный JSON-объект в формате PriceRecommendationRequest.
    Валидация выполняется поэлементно на уровне сервиса (не Pydantic на входе целиком),
    чтобы одна некорректная позиция не роняла весь пакет — см. app/services/recommendation.py.
    """

    model_config = ConfigDict(extra="forbid")

    items: List[Dict[str, Any]] = Field(..., min_length=1, max_length=200)


class BatchRecommendationItemResult(BaseModel):
    index: int
    ok: bool
    item_id: Optional[str] = None
    result: Optional[PriceRecommendationResponse] = None
    error: Optional[str] = None


class BatchPriceRecommendationResponse(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: List[BatchRecommendationItemResult]
    calculation_timestamp: str
