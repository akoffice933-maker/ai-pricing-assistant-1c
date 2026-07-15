# Контракт данных Этапа 2

## Endpoint

```http
POST /skills/recommend_price
Content-Type: application/json
```

## Запрос

```json
{
  "request_id": "uuid",
  "user_id": "manager_1",
  "business_goal": "maximize_profit",
  "horizon_days": 30,
  "item": {
    "item_id": "000000123",
    "item_type": "product",
    "item_name": "Наушники X200",
    "category": "wireless_headphones",
    "current_price": 179.0,
    "unit_cost": 128.0,
    "price_unit": "unit",
    "currency": "EUR",
    "sales_last_30_days": 240,
    "sales_last_90_days": 620,
    "stock_quantity": 180,
    "available_capacity": null,
    "team_utilization_percent": null,
    "target_margin_percent": 30,
    "quality_index": 1.08
  },
  "market_context": {
    "market_category": "wireless_headphones",
    "region": "LV",
    "channel": "online",
    "market_price_median": 189.0,
    "market_demand_index": 1.18,
    "promo_share": 0.35,
    "availability_index": 0.78,
    "seasonality_index": 1.2,
    "data_freshness_days": 3,
    "coverage_score": 0.78,
    "confidence": 0.82
  },
  "constraints": {
    "min_margin_percent": 20,
    "max_price_increase_percent": 20,
    "max_price_decrease_percent": 30,
    "price_ending": 0.99,
    "min_confidence_for_apply": 0.70
  }
}
```

## Ответ

```json
{
  "request_id": "uuid",
  "item_id": "000000123",
  "item_name": "Наушники X200",
  "item_type": "product",
  "market_category": "wireless_headphones",
  "business_goal": "maximize_profit",
  "current_price": 179.0,
  "recommended_price": 189.99,
  "price_change_percent": 6.14,
  "expected_demand": 225.0,
  "expected_revenue": 42747.75,
  "expected_gross_profit": 13947.75,
  "expected_margin_percent": 32.63,
  "confidence": 0.78,
  "is_reliable": true,
  "demand_curve": [],
  "elasticity": -1.8,
  "market_context_summary": {},
  "explanation": {},
  "warnings": [],
  "recommended_action": {
    "type": "create_price_change_draft",
    "requires_approval": true,
    "document_type": "УстановкаЦенНоменклатуры"
  },
  "model_version": "demand_curve_v1.0.0-market-relative+price_optimizer_v1.0.0",
  "calculation_timestamp": "2026-07-15T00:00:00Z"
}
```

## Обязательные поля для MVP

### `item`

- `item_id`
- `item_type`
- `item_name`
- `category`
- `current_price`
- `unit_cost`
- `sales_last_30_days` или `sales_last_90_days`

### `market_context`

- `market_category`
- `market_price_median`
- `market_demand_index`
- `promo_share`
- `availability_index`
- `seasonality_index`
- `data_freshness_days`
- `confidence`

## Маппинг 1С → item

| JSON | 1С-источник |
|---|---|
| `item_id` | Уникальный идентификатор номенклатуры |
| `item_type` | Вид/тип номенклатуры или регистр маппинга |
| `item_name` | Номенклатура.Наименование |
| `current_price` | Регистр цен |
| `unit_cost` | Себестоимость/стоимость часа/логистика/комиссии |
| `sales_last_30_days` | Регистр продаж/актов/часов |
| `stock_quantity` | Регистр остатков |
| `available_capacity` | Для услуг: доступные часы/мощность |
| `quality_index` | Рейтинг/бренд/SLA/маппинг |

## Маппинг 1С → market_context

| JSON | 1С-источник |
|---|---|
| `market_category` | `AI_МаппингРыночныхКатегорий` |
| `region` | маппинг/константа |
| `channel` | маппинг/константа |
| `market_price_median` | `AI_РыночныеИндикаторы.MarketPriceMedian` |
| `market_demand_index` | `AI_РыночныеИндикаторы.MarketDemandIndex` |
| `promo_share` | `AI_РыночныеИндикаторы.PromoShare` |
| `availability_index` | `AI_РыночныеИндикаторы.AvailabilityIndex` |
| `confidence` | `AI_РыночныеИндикаторы.Confidence` |
