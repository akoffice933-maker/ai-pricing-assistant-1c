"""Оркестратор: DemandCurveSkill -> PriceOptimizerSkill -> единый ответ recommend_price."""

from typing import List

from pydantic import ValidationError

from app.schemas import (
    BatchPriceRecommendationRequest,
    BatchPriceRecommendationResponse,
    BatchRecommendationItemResult,
    DemandCurveRequest,
    PriceOptimizationRequest,
    PriceRecommendationRequest,
    PriceRecommendationResponse,
)
from app.services.demand_curve import DemandCurveSkill
from app.services.price_optimizer import PriceOptimizerSkill
from app.utils import now_iso

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


def build_batch_recommendations(request: BatchPriceRecommendationRequest) -> BatchPriceRecommendationResponse:
    """Считает рекомендацию по каждой позиции пакета независимо.

    Некорректная позиция (не проходит валидацию PriceRecommendationRequest) или ошибка
    расчёта не роняют весь пакет — попадает в results с ok=False и текстом ошибки,
    остальные позиции считаются как обычно.
    """
    results: List[BatchRecommendationItemResult] = []
    succeeded = 0
    for index, raw_item in enumerate(request.items):
        item_id = None
        if isinstance(raw_item, dict):
            item_id = (raw_item.get("item") or {}).get("item_id") if isinstance(raw_item.get("item"), dict) else None
        try:
            item_request = PriceRecommendationRequest(**raw_item)
            recommendation = build_recommendation(item_request)
            results.append(
                BatchRecommendationItemResult(
                    index=index,
                    ok=True,
                    item_id=recommendation.item_id,
                    result=recommendation,
                )
            )
            succeeded += 1
        except ValidationError as exc:
            results.append(
                BatchRecommendationItemResult(
                    index=index,
                    ok=False,
                    item_id=item_id,
                    error=f"Ошибка валидации: {exc.errors()[0]['msg'] if exc.errors() else str(exc)}",
                )
            )
        except Exception as exc:  # noqa: BLE001 - изолируем ошибку одной позиции от остальных
            results.append(
                BatchRecommendationItemResult(index=index, ok=False, item_id=item_id, error=str(exc))
            )

    return BatchPriceRecommendationResponse(
        total=len(request.items),
        succeeded=succeeded,
        failed=len(request.items) - succeeded,
        results=results,
        calculation_timestamp=now_iso(),
    )
