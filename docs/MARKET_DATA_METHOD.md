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

**Ни один из proxy-сигналов ниже нигде в проекте не реализован.** Формула существует только на
бумаге — `search_trend_index`, `lead_volume_index`, `category_views_index` нужно собирать и подавать
отдельным pipeline'ом, которого пока нет. Единственный реально работающий путь — второй вариант
(fallback), и он тихо подменяет «рыночный спрос» календарной сезонностью, а не реальным сигналом
спроса.

Если есть proxy-сигналы (пока — гипотетически):

```text
market_demand_index = 0.75 × avg(search_trend_index, lead_volume_index, category_views_index)
                    + 0.25 × seasonality_index
```

Если proxy-сигналов нет (текущая реальность MVP):

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

## Baseline и forecast market

Чтобы рыночный индекс не сокращался при калибровке по историческим продажам, модель разделяет:

```text
baseline_market_*  — рынок периода, из которого взяты sales_last_30/90
forecast market_context — рынок периода, для которого строится рекомендация
```

Если baseline не передан, MVP считает baseline нормальным рынком:

```text
baseline_market_demand_index = 1.0
baseline_promo_share = 0.0
baseline_availability_index = 1.0
```

## Важное правило сезонности

В MVP `market_demand_index`, рассчитанный из `/market/calculate_indicators`, уже включает сезонность. Поэтому в demand model он не умножается на `seasonality_index` повторно.

## Production

В production эти правила нужно заменить обучаемой моделью/калибровкой по истории:

```text
история цен + история спроса + baseline market + forecast market → эластичность и спрос
```
