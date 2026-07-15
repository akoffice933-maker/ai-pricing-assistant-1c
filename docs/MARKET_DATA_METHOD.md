# Методика рыночных индикаторов

## Минимальный market_context

```json
{
  "market_category": "wireless_headphones",
  "region": "LV",
  "channel": "online",
  "market_price_median": 189,
  "market_demand_index": 1.18,
  "promo_share": 0.35,
  "availability_index": 0.78,
  "seasonality_index": 1.2,
  "data_freshness_days": 3,
  "coverage_score": 0.78,
  "confidence": 0.82
}
```

## Relative price

```text
relative_price = our_price / market_price_median
```

## Value-adjusted relative price

```text
value_adjusted_relative_price = relative_price / quality_index
```

`quality_index > 1` означает, что позиция имеет ценностную премию: рейтинг, бренд, SLA, скорость доставки, экспертиза.

## Market demand index

Если есть proxy-сигналы:

```text
market_demand_index = 0.75 × avg(search_trend_index, lead_volume_index, category_views_index)
                    + 0.25 × seasonality_index
```

Если proxy-сигналов нет:

```text
market_demand_index = seasonality_index
```

## Confidence

MVP-правило:

```text
coverage_score = min(1, observation_count / 15)
confidence = (0.30 + 0.60 × coverage_score) × freshness_penalty
```

Где:

```text
freshness_penalty = 1.00, если данные свежие
freshness_penalty = 0.82, если data_freshness_days > 14
freshness_penalty = 0.65, если data_freshness_days > 30
```

## Production

В production эти правила нужно заменить обучаемой моделью/калибровкой по истории:

```text
история цен + история спроса + рынок → эластичность и спрос
```
