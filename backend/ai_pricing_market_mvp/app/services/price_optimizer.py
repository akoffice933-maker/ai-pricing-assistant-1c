"""PriceOptimizerSkill — выбор цены по кривой спроса под бизнес-цель и ограничения."""

import math
from typing import Any, Dict, List, Optional

from app.schemas import (
    BusinessGoal,
    DemandPoint,
    ItemData,
    PriceOptimizationRequest,
    PriceOptimizationResponse,
)
from app.utils import clamp, now_iso, safe_div


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
