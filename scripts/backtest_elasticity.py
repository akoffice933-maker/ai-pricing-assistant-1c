#!/usr/bin/env python3
"""Backtesting-харнесс для эвристической эластичности спроса.

Отвечает на вопрос из ревью: "насколько прогноз спроса по кривой (Q(p)) расходится
с тем, что реально произошло по факту продаж?" — до сих пор эластичность была
константой-эвристикой, не проверенной ни на одном историческом наблюдении.

ВАЖНО: этот скрипт — инструмент, а не готовый результат валидации. Пока в проекте
нет накопленной истории вида "при цене P и таком-то рыночном контексте фактически
продали N штук", прогонять его не на чём. examples/backtest_sample.csv — синтетический
пример на 8 строк ТОЛЬКО чтобы показать, что харнесс работает end-to-end; он не
доказывает точность модели на реальных данных.

Использование:
    python scripts/backtest_elasticity.py backend/ai_pricing_market_mvp/examples/backtest_sample.csv

Формат входного CSV — см. examples/backtest_sample.csv и docstring ниже у load_rows().
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend" / "ai_pricing_market_mvp"))

from main import DemandCurveRequest, ItemData, MarketContext, demand_skill  # noqa: E402


REQUIRED_COLUMNS = [
    "item_id",
    "item_type",
    "category",
    "price",
    "actual_demand",
    "unit_cost",
    "quality_index",
    "sales_last_30_days",
    "sales_last_90_days",
    "market_price_median",
    "market_demand_index",
    "promo_share",
    "availability_index",
    "seasonality_index",
    "data_freshness_days",
    "coverage_score",
    "confidence",
]


def load_rows(csv_path: Path) -> List[Dict[str, Any]]:
    """Читает CSV с историческими наблюдениями цена -> факт. продажи.

    Обязательные колонки перечислены в REQUIRED_COLUMNS. Каждая строка — это один
    исторический период (например, месяц) для одной позиции: цена, которая
    действовала, фактический спрос за период, и рыночный контекст ЭТОГО периода
    (используется одновременно как baseline при калибровке, так и forecast — в
    backtest мы не пытаемся предсказать сдвиг рынка, только форму кривой спроса).
    """
    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = set(REQUIRED_COLUMNS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"В CSV не хватает колонок: {sorted(missing)}")
        return list(reader)


def predict_demand_for_row(row: Dict[str, Any]) -> float:
    item = ItemData(
        item_id=row["item_id"],
        item_type=row["item_type"],
        item_name=row["item_id"],
        category=row["category"],
        current_price=float(row["price"]),
        unit_cost=float(row["unit_cost"]),
        quality_index=float(row["quality_index"]),
        sales_last_30_days=float(row["sales_last_30_days"]),
        sales_last_90_days=float(row["sales_last_90_days"]),
    )
    market = MarketContext(
        market_category=row["category"],
        market_price_median=float(row["market_price_median"]),
        market_demand_index=float(row["market_demand_index"]),
        promo_share=float(row["promo_share"]),
        availability_index=float(row["availability_index"]),
        seasonality_index=float(row["seasonality_index"]),
        data_freshness_days=float(row["data_freshness_days"]),
        coverage_score=float(row["coverage_score"]),
        confidence=float(row["confidence"]),
    )
    request = DemandCurveRequest(
        item=item,
        market_context=market,
        # API требует минимум 2 точки в сетке; вторая — чисто техническая, нужна нам
        # только точка с фактической исторической ценой.
        price_grid=[float(row["price"]), float(row["price"]) * 1.001],
        # Backtest не моделирует сдвиг рынка между периодом калибровки и периодом
        # прогноза — baseline совпадает с forecast-контекстом этой же строки.
        baseline_market_price_median=market.market_price_median,
        baseline_market_demand_index=market.market_demand_index,
        baseline_promo_share=market.promo_share,
        baseline_availability_index=market.availability_index,
    )
    response = demand_skill.forecast(request)
    target_price = float(row["price"])
    point = min(response.demand_curve, key=lambda p: abs(p.price - target_price))
    return point.expected_demand


def run_backtest(csv_path: Path) -> int:
    rows = load_rows(csv_path)
    if not rows:
        print("Пустой CSV — нечего проверять.", file=sys.stderr)
        return 1

    errors: List[float] = []
    abs_pct_errors: List[float] = []
    signed_pct_errors: List[float] = []  # для оценки систематического смещения (bias)
    per_category: Dict[str, List[float]] = {}

    print(f"{'item_id':<14} {'price':>8} {'actual':>8} {'predicted':>10} {'err %':>8}")
    print("-" * 54)
    for row in rows:
        actual = float(row["actual_demand"])
        predicted = predict_demand_for_row(row)
        err = predicted - actual
        pct_err = (err / actual * 100) if actual else float("nan")

        errors.append(abs(err))
        if actual:
            abs_pct_errors.append(abs(pct_err))
            signed_pct_errors.append(pct_err)
        per_category.setdefault(row["category"], []).append(abs(pct_err) if actual else 0.0)

        print(f"{row['item_id']:<14} {float(row['price']):>8.2f} {actual:>8.1f} {predicted:>10.1f} {pct_err:>7.1f}%")

    print("-" * 54)
    print(f"MAE (абс. ошибка спроса):      {statistics.mean(errors):.2f}")
    if abs_pct_errors:
        print(f"MAPE (сред. ошибка, %):         {statistics.mean(abs_pct_errors):.1f}%")
    if signed_pct_errors:
        bias = statistics.mean(signed_pct_errors)
        direction = "завышает" if bias > 0 else "занижает"
        print(f"Смещение (bias, %):             {bias:+.1f}%  ({direction} спрос систематически, если |bias| велик)")
    print()
    print("По категориям (MAPE, %):")
    for category, errs in per_category.items():
        print(f"  {category:<20} {statistics.mean(errs):.1f}%")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv_path", type=Path, help="Путь к CSV с историческими наблюдениями")
    args = parser.parse_args()
    return run_backtest(args.csv_path)


if __name__ == "__main__":
    raise SystemExit(main())
