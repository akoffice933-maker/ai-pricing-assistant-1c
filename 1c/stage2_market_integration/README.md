# Этап 2 — 1С-интеграция Market-aware Pricing

Этот пакет переводит 1С-интеграцию AI Pricing Assistant на новую архитектуру:

```text
Market Context → Demand Curve → Price Optimization → 1С audit/action
```

В отличие от первой версии, система **не прогнозирует цену напрямую**. 1С передаёт:

- внутренние данные позиции: цена, себестоимость, продажи, остатки/мощность;
- рыночный контекст: медиана рынка, индекс общего спроса, промо-давление, доступность, сезонность;

FastAPI возвращает:

- рекомендованную цену;
- кривую спроса;
- ожидаемый спрос;
- ожидаемую выручку;
- ожидаемую валовую прибыль;
- объяснение;
- JSON-аудит.

## Что входит в Этап 2

```text
ai_pricing_stage2_1c_market_integration/
├── README.md
├── metadata/
│   ├── METADATA_STAGE2.md
│   └── FORM_SPEC_STAGE2.md
├── common_modules/
│   ├── AIPricingMarketContextServer.bsl
│   ├── AIPricingMarketIndicatorsLoaderServer.bsl
│   ├── AIPricingDataProviderMarketServer.bsl
│   ├── AIPricingRecommendationsMarketServer.bsl
│   └── AIPricingStage2TestsServer.bsl
├── forms/
│   ├── AI_MarketRecommendationsFormModule.bsl
│   └── AI_MarketIndicatorsLoaderFormModule.bsl
├── examples/
│   ├── market_indicators_sample.json
│   ├── market_indicators_sample.csv
│   ├── product_market_request.json
│   └── service_market_request.json
├── docs/
│   ├── MIGRATION_FROM_STAGE1.md
│   ├── ACCEPTANCE_TESTS.md
│   └── DATA_CONTRACT.md
└── tests/
    └── manual_test_script.md
```

## Главные изменения относительно Этапа 1

### 1. Новый регистр `AI_РыночныеИндикаторы`

Хранит рыночные показатели:

- `MarketPriceMedian`;
- `MarketDemandIndex`;
- `PromoShare`;
- `AvailabilityIndex`;
- `SeasonalityIndex`;
- `Confidence`;
- `RawDataJSON`.

### 2. Новый регистр маппинга `AI_МаппингРыночныхКатегорий`

Связывает номенклатуру/группу/вид номенклатуры с рыночной категорией:

```text
1С.Номенклатура → market_category + region + channel + item_type
```

### 3. Обновление `AI_РекомендацииПоЦенам`

Добавляются поля:

- `MarketContextJSON`;
- `КриваяСпросаJSON`;
- `Эластичность`;
- `MarketPriceMedian`;
- `MarketDemandIndex`;
- `RelativePriceCurrent`;
- `RelativePriceRecommended`;
- `ExpectedDemand`;
- `ExpectedRevenue`;
- `ExpectedGrossProfit`.

### 4. Новый серверный data provider

`AIPricingDataProviderMarketServer.bsl` формирует новый JSON:

```json
{
  "item": {},
  "market_context": {},
  "business_goal": "maximize_profit",
  "constraints": {}
}
```

### 5. Загрузчик рыночных индикаторов

`AIPricingMarketIndicatorsLoaderServer.bsl` умеет загружать индикаторы из:

- JSON-массива;
- CSV-строки.

## Как интегрировать

1. Взять предыдущий пакет `ai_pricing_1c_integration_skeleton`.
2. Добавить объекты из `metadata/METADATA_STAGE2.md`.
3. Добавить общие модули из `common_modules/`.
4. Обновить форму рекомендаций или создать новую форму по `forms/AI_MarketRecommendationsFormModule.bsl`.
5. Добавить форму загрузчика индикаторов `forms/AI_MarketIndicatorsLoaderFormModule.bsl`.
6. Запустить FastAPI из `ai_pricing_market_mvp`.
7. Загрузить тестовые рыночные индикаторы из `examples/market_indicators_sample.json` или `.csv`.
8. Выполнить тестовые сценарии из `docs/ACCEPTANCE_TESTS.md`.

## Важное правило

AI по-прежнему не проводит документы.

```text
AI рекомендует → 1С сохраняет аудит → человек подтверждает → создаётся непроведённый документ
```

