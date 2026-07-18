"""DemandCurveSkill — прогноз кривой спроса относительно рынка."""

import math
from typing import List

from app.schemas import (
    DemandCurveRequest,
    DemandCurveResponse,
    DemandPoint,
    ItemData,
    ItemType,
    MarketContext,
)
from app.utils import clamp, now_iso, safe_div


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
