# Ручной тестовый сценарий Этапа 2

## Подготовка

1. Запустить FastAPI:

```bash
cd ai_pricing_market_mvp
uvicorn main:app --reload --port 8000
```

2. Проверить:

```bash
curl http://localhost:8000/health
```

3. В 1С заполнить настройки:

```text
AI_Pricing_Host = localhost
AI_Pricing_Port = 8000
AI_Pricing_UseHTTPS = Ложь
AI_Pricing_DefaultBusinessGoal = maximize_profit
```

## Загрузка индикаторов

1. Открыть форму `AI_MarketIndicatorsLoader`.
2. Вставить JSON из `examples/market_indicators_sample.json`.
3. Нажать `Загрузить`.
4. Проверить записи в `AI_РыночныеИндикаторы`.

## Маппинг категории

1. Добавить запись в `AI_МаппингРыночныхКатегорий`:

```text
ГруппаНоменклатуры = Наушники
КатегорияРынка = wireless_headphones
Регион = LV
КаналПродаж = online
ТипПозиции = product
PriceUnit = unit
QualityIndex = 1.08
Активен = Истина
```

2. Для услуги:

```text
ГруппаНоменклатуры = Консалтинг 1С
КатегорияРынка = 1c_implementation_services
Регион = LV
КаналПродаж = b2b_direct
ТипПозиции = service
PriceUnit = hour
QualityIndex = 1.18
Активен = Истина
```

## Расчёт

1. Открыть форму `AI_MarketRecommendations`.
2. Выбрать товар.
3. Нажать `РассчитатьMarketAwareДляТовара`.
4. Проверить:
   - рекомендация появилась в списке;
   - заполнена кривая спроса;
   - заполнены рыночные индексы;
   - цена не применена автоматически.

## Документ

1. Выбрать рекомендацию.
2. Нажать `СоздатьДокументЦен`.
3. Проверить, что документ создан непроведённым.
