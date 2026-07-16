# Review fixes

Дата: 2026-07-15

Этот документ фиксирует изменения, выполненные после ревью проекта.

## Исправлено P0

### 1. Market demand index теперь влияет на demand curve

Проблема: при калибровке по историческим продажам `market_demand_index` сокращался, потому что один и тот же market context использовался и как baseline, и как forecast.

Исправление:

- добавлены baseline-поля:
  - `baseline_market_price_median`;
  - `baseline_market_demand_index`;
  - `baseline_promo_share`;
  - `baseline_availability_index`;
- demand model теперь разделяет:

```text
baseline market — период исторических продаж
forecast market — период рекомендации
```

Формула:

```text
base_demand = observed_demand / (baseline_market * baseline_competition * baseline_price_response)
forecast_demand = base_demand * forecast_market * forecast_competition * price_response
```

### 2. Fallback optimizer больше не нарушает ограничения

Проблема: если ни одна точка кривой спроса не проходила ограничения, fallback мог вернуть цену ниже минимальной маржи или выше лимита изменения.

Исправление:

- fallback-точка принудительно приводится к диапазону `[lower_bound, upper_bound]`;
- экономика пересчитывается после изменения цены.

### 3. Округление `.99` больше не нарушает границы

Проблема: психологическое округление могло поднять цену выше `upper_bound`.

Исправление:

```python
bounded_price = clamp(rounded_price, lower_bound, upper_bound)
```

### 4. Backend ↔ 1С контракт синхронизирован

Добавлено в response:

- `price_unit`;
- `currency`;
- полный `market_context_summary`, включая:
  - `region`;
  - `channel`;
  - `period`;
  - `coverage_score`;
  - `source_count`.

### 5. 1С запись `PriceUnit`

В `AIPricingRecommendationsMarketServer.bsl` добавлена запись:

```bsl
Запись.PriceUnit = ПолучитьСвойство(Результат, "price_unit", "");
```

## Исправлено P1

### 1. Убрано двойное применение сезонности

`market_demand_index`, рассчитанный из `/market/calculate_indicators`, уже включает сезонность. Поэтому demand model теперь использует:

```python
return market.market_demand_index
```

а не:

```python
market.market_demand_index * market.seasonality_index
```

### 2. Убрано двойное штрафование confidence за coverage/freshness

`market.confidence` теперь считается уже итоговой оценкой качества рыночных данных. В point confidence добавляются только model-specific penalties:

- мало исторических продаж;
- большая дистанция цены от текущей.

### 3. Добавлены dev requirements и CI tests

Добавлен файл:

```text
backend/ai_pricing_market_mvp/requirements-dev.txt
```

CI теперь устанавливает dev-зависимости и запускает:

```bash
pytest -q
```

### 4. Smoke tests переименованы и расширены

Файл:

```text
backend/ai_pricing_market_mvp/test_smoke.py
```

Покрывает:

- `/health`;
- `/market/calculate_indicators`;
- `/market/calculate_indicators/export_1c`;
- `/skills/recommend_price`;
- влияние `market_demand_index` на кривую;
- соблюдение минимальной маржи после fallback/rounding.

### 5. Добавлен export endpoint для 1С loader

Новый endpoint:

```text
POST /market/calculate_indicators/export_1c
```

Возвращает JSON-массив записей, совместимый с загрузчиком 1С.

### 6. Исправлен BSL-парсинг чисел

Убран потенциально проблемный вызов:

```bsl
Символы.РазделительДробнойЧасти
```

Заменён на безопасную попытку преобразования через `,` и `.`.

## Проверка

Локально выполнено:

```bash
python -m py_compile backend/ai_pricing_market_mvp/main.py scripts/calculate_market_indicators.py
cd backend/ai_pricing_market_mvp
pytest -q
```

Результат:

```text
6 passed
```
