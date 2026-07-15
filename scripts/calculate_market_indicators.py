#!/usr/bin/env python3
"""Calculate AI_РыночныеИндикаторы JSON from raw competitor CSV.

Input CSV columns:
    market_category,region,channel,item_type,price,competitor_id,source,is_promo,is_available,delivery_days,data_freshness_days

Example:
    python scripts/calculate_market_indicators.py \
      --input docs/examples/raw_market_observations.csv \
      --output market_indicators.json

The output is compatible with the 1C loader `AIPricingMarketIndicatorsLoaderServer.ЗагрузитьИзJSONСтроки`.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import mean
from typing import Any


def as_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    return float(str(value).replace(",", "."))


def as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "да", "истина"}


def percentile(values: list[float], q: float) -> float:
    values = sorted(values)
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    pos = (len(values) - 1) * q
    low = math.floor(pos)
    high = math.ceil(pos)
    if low == high:
        return values[int(pos)]
    return values[low] * (high - pos) + values[high] * (pos - low)


def build_indicator(rows: list[dict[str, str]]) -> dict[str, Any]:
    prices = [as_float(row["price"]) for row in rows if as_float(row.get("price"), 0) > 0]
    if not prices:
        raise ValueError("Group has no positive prices")

    first = rows[0]
    count = len(rows)
    sources = {row.get("source", "manual") for row in rows if row.get("source")}
    competitors = {row.get("competitor_id", "") for row in rows if row.get("competitor_id")}
    promo_share = sum(1 for row in rows if as_bool(row.get("is_promo"))) / count
    availability_index = sum(1 for row in rows if as_bool(row.get("is_available", "true"))) / count
    delivery_values = [as_float(row.get("delivery_days"), 0) for row in rows if row.get("delivery_days") not in {None, ""}]
    freshness = max(int(as_float(row.get("data_freshness_days"), 0)) for row in rows)

    coverage_score = min(1.0, max(0.05, count / 15))
    freshness_penalty = 0.65 if freshness > 30 else 0.82 if freshness > 14 else 1.0
    confidence = min(0.95, max(0.05, (0.30 + 0.60 * coverage_score) * freshness_penalty))

    search_trend_index = as_float(first.get("search_trend_index"), 0) or None
    lead_volume_index = as_float(first.get("lead_volume_index"), 0) or None
    category_views_index = as_float(first.get("category_views_index"), 0) or None
    seasonality_index = as_float(first.get("seasonality_index"), 1) or 1

    demand_signals = [v for v in [search_trend_index, lead_volume_index, category_views_index] if v is not None]
    market_demand_index = (sum(demand_signals) / len(demand_signals) * 0.75 + seasonality_index * 0.25) if demand_signals else seasonality_index

    return {
        "period": first.get("period") or date.today().strftime("%Y-%m"),
        "market_category": first["market_category"],
        "region": first.get("region") or "LV",
        "channel": first.get("channel") or "online",
        "item_type": first.get("item_type") or "product",
        "source": "calculated_csv",
        "market_price_min": round(min(prices), 2),
        "market_price_p25": round(percentile(prices, 0.25), 2),
        "market_price_median": round(percentile(prices, 0.50), 2),
        "market_price_avg": round(mean(prices), 2),
        "market_price_p75": round(percentile(prices, 0.75), 2),
        "market_price_max": round(max(prices), 2),
        "competitor_count": len(competitors) if competitors else count,
        "active_competitor_count": sum(1 for row in rows if as_bool(row.get("is_available", "true"))),
        "market_demand_index": round(market_demand_index, 4),
        "search_trend_index": search_trend_index,
        "lead_volume_index": lead_volume_index,
        "category_views_index": category_views_index,
        "promo_share": round(promo_share, 4),
        "availability_index": round(availability_index, 4),
        "average_delivery_days": round(mean(delivery_values), 2) if delivery_values else None,
        "seasonality_index": seasonality_index,
        "data_freshness_days": freshness,
        "source_count": len(sources),
        "coverage_score": round(coverage_score, 4),
        "confidence": round(confidence, 4),
        "currency": first.get("currency") or "EUR",
        "calculation_method": "scripts/calculate_market_indicators.py",
        "comment": f"Calculated from {count} raw observations",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    groups: dict[tuple[str, str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    with args.input.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (
                row.get("period") or date.today().strftime("%Y-%m"),
                row["market_category"],
                row.get("region") or "LV",
                row.get("channel") or "online",
                row.get("item_type") or "product",
            )
            groups[key].append(row)

    indicators = [build_indicator(rows) for rows in groups.values()]
    args.output.write_text(json.dumps(indicators, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Written {len(indicators)} market indicator records to {args.output}")


if __name__ == "__main__":
    main()
