"""Расчёт рыночных индикаторов из сырых наблюдений."""

from app.schemas import MarketContext, MarketIndicatorsCalculationRequest, MarketIndicatorsCalculationResponse
from app.utils import clamp, now_iso, percentile


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
