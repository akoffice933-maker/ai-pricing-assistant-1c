# AI Pricing Assistant — Market Demand MVP

Это рабочий MVP новой архитектуры ценообразования:

```text
Market Context → Demand Curve → Price Optimization → 1С audit/action
```

Главная идея:

> Система не прогнозирует цену напрямую. Она оценивает общий рынок, строит кривую спроса при разных ценах относительно рынка и выбирает цену под бизнес-цель.

## Что реализовано

FastAPI-сервис с тремя навыками:

| Endpoint | Назначение |
|---|---|
| `POST /skills/forecast_demand_curve` | Строит кривую спроса `цена → ожидаемый спрос` с учётом рыночных индикаторов. |
| `POST /skills/optimize_price` | Выбирает цену по готовой кривой спроса и ограничениям. |
| `POST /skills/recommend_price` | Оркестратор: строит кривую спроса и оптимизирует цену одним вызовом. |
| `POST /market/calculate_indicators` | Считает `market_context` из сырых рыночных наблюдений. |
| `POST /market/calculate_indicators/export_1c` | Возвращает массив записей для загрузчика 1С `AI_РыночныеИндикаторы`. |

Поддерживаются:

- товары;
- услуги;
- подписки;
- проекты;
- рыночные индикаторы;
- относительная цена к медиане рынка;
- value-adjusted relative price;
- бизнес-цели;
- ограничения минимальной маржи и максимального изменения цены;
- объяснение и JSON-аудит.

## Быстрый запуск

```bash
cd ai_pricing_market_mvp
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Swagger:

```text
http://localhost:8000/docs
```

## Примеры curl

```bash
curl -X POST http://localhost:8000/skills/recommend_price \
  -H "Content-Type: application/json" \
  --data @examples/product_recommend_price.json | python -m json.tool
```

```bash
curl -X POST http://localhost:8000/skills/recommend_price \
  -H "Content-Type: application/json" \
  --data @examples/service_recommend_price.json | python -m json.tool
```

## Авторизация

По умолчанию локально токен не требуется.

Чтобы включить Bearer token:

```bash
export AI_PRICING_API_TOKEN="secret-token"
uvicorn main:app --reload --port 8000
```

И передавать:

```http
Authorization: Bearer secret-token
```

## Ключевые сущности

### `ItemData`

Универсальная позиция:

- `item_type`: `product`, `service`, `subscription`, `project`;
- `current_price`;
- `unit_cost`;
- `sales_last_30_days`;
- `sales_last_90_days`;
- `stock_quantity` для товаров;
- `available_capacity` / `team_utilization_percent` для услуг;
- `quality_index` — премия ценности: рейтинг, бренд, SLA, экспертиза.

### `MarketContext`

Индикаторы общего рынка:

- `market_price_median`;
- `market_demand_index`;
- `promo_share`;
- `availability_index`;
- `seasonality_index`;
- `competitor_count`;
- `data_freshness_days`;
- `confidence`.

## Формула MVP

```text
Q(p) = base_demand
     × market_multiplier
     × competitive_multiplier
     × (value_adjusted_relative_price ^ elasticity)
```

Где:

```text
relative_price = our_price / market_price_median
value_adjusted_relative_price = relative_price / quality_index
```

MVP калибрует базовый спрос по фактическим продажам 1С и текущей относительной цене.

## Production-следующий шаг

В production нужно заменить эвристическую эластичность на обучаемую модель:

```text
история цен + история спроса + рыночные индикаторы → elasticity / demand model
```

Минимальные данные:

- цена по датам;
- продажи/лиды/сделки по датам;
- медиана рынка по датам;
- индекс общего спроса по датам;
- промо конкурентов;
- наличие конкурентов;
- сезонность;
- канал/регион;
- себестоимость/стоимость часа.

## Связь с 1С

В папке `1c/` есть skeleton для регистра `AI_РыночныеИндикаторы` и серверного модуля, который формирует `MarketContext` из 1С.



## Тесты

```bash
pip install -r requirements-dev.txt
pytest -q
```
