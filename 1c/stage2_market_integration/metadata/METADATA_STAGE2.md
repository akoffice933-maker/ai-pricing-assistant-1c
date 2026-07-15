# Метаданные Этапа 2

## 1. Новый регистр сведений `AI_РыночныеИндикаторы`

Тип: периодический регистр сведений. Рекомендуемая периодичность — `День` или `Месяц`.

Назначение: хранить индикаторы общего рынка для построения кривой спроса.

### Измерения

| Имя | Тип | Комментарий |
|---|---|---|
| `КатегорияРынка` | Строка(150) | Например `wireless_headphones`, `1c_implementation_services`. |
| `Регион` | Строка(50) | Например `LV`, `Riga`, `EU`. |
| `КаналПродаж` | Строка(50) | `online`, `retail`, `marketplace`, `b2b_direct`. |
| `ТипПозиции` | Строка(30) | `product`, `service`, `subscription`, `project`. |
| `ИсточникДанных` | Строка(100) | `manual`, `competitor_parser`, `crm`, `marketplace`, `google_trends`. |

### Ресурсы

| Имя | Тип | JSON-поле |
|---|---|---|
| `MarketPriceMin` | Число(15,2) | `market_price_min` |
| `MarketPriceP25` | Число(15,2) | `market_price_p25` |
| `MarketPriceMedian` | Число(15,2) | `market_price_median` |
| `MarketPriceAvg` | Число(15,2) | `market_price_avg` |
| `MarketPriceP75` | Число(15,2) | `market_price_p75` |
| `MarketPriceMax` | Число(15,2) | `market_price_max` |
| `CompetitorCount` | Число(10,0) | `competitor_count` |
| `ActiveCompetitorCount` | Число(10,0) | `active_competitor_count` |
| `MarketDemandIndex` | Число(8,4) | `market_demand_index` |
| `SearchTrendIndex` | Число(8,4) | `search_trend_index` |
| `LeadVolumeIndex` | Число(8,4) | `lead_volume_index` |
| `CategoryViewsIndex` | Число(8,4) | `category_views_index` |
| `PromoShare` | Число(6,4) | `promo_share` |
| `AverageDiscountPercent` | Число(8,2) | `average_discount_percent` |
| `AvailabilityIndex` | Число(6,4) | `availability_index` |
| `StockoutRate` | Число(6,4) | `stockout_rate` |
| `AverageDeliveryDays` | Число(8,2) | `average_delivery_days` |
| `SeasonalityIndex` | Число(8,4) | `seasonality_index` |
| `TenderCount` | Число(10,0) | `tender_count` |
| `ConversionBenchmark` | Число(6,4) | `conversion_benchmark` |
| `SpecialistSupplyIndex` | Число(8,4) | `specialist_supply_index` |
| `WageIndex` | Число(8,4) | `wage_index` |
| `DataFreshnessDays` | Число(5,0) | `data_freshness_days` |
| `SourceCount` | Число(5,0) | `source_count` |
| `CoverageScore` | Число(6,4) | `coverage_score` |
| `Confidence` | Число(6,4) | `confidence` |

### Реквизиты

| Имя | Тип | Комментарий |
|---|---|---|
| `Currency` | Строка(8) | Валюта рыночных цен. |
| `RawDataJSON` | Строка неограниченной длины | Исходные данные источника. |
| `CalculationMethod` | Строка(250) | Метод расчёта индексов. |
| `LoadedAt` | Дата | Когда загружено. |
| `Comment` | Строка неограниченной длины | Комментарий. |

### Индексы

- `КатегорияРынка, Регион, КаналПродаж, ТипПозиции, Период`.
- `ИсточникДанных, Период`.

---

## 2. Новый регистр сведений `AI_МаппингРыночныхКатегорий`

Тип: независимый непериодический регистр сведений.

Назначение: маппинг объектов 1С на рыночные категории.

### Измерения

| Имя | Тип | Комментарий |
|---|---|---|
| `Номенклатура` | СправочникСсылка.Номенклатура | Можно не заполнять, если маппинг задан по группе. |
| `ГруппаНоменклатуры` | СправочникСсылка.Номенклатура | Группа/родитель. |
| `ВидНоменклатуры` | СправочникСсылка.ВидыНоменклатуры / строка | Если есть в конфигурации. |

### Реквизиты

| Имя | Тип | Комментарий |
|---|---|---|
| `КатегорияРынка` | Строка(150) | Для market_context. |
| `Регион` | Строка(50) | По умолчанию `LV`. |
| `КаналПродаж` | Строка(50) | По умолчанию `online`. |
| `ТипПозиции` | Строка(30) | `product`/`service`. |
| `PriceUnit` | Строка(30) | `unit`, `hour`, `project`, `month`. |
| `QualityIndex` | Число(6,4) | Индекс ценности/качества. |
| `Активен` | Булево | Использовать маппинг. |
| `Комментарий` | Строка неограниченной длины | Пояснение. |

---

## 3. Обновление регистра `AI_РекомендацииПоЦенам`

К существующему регистру из Этапа 1 добавить реквизиты/ресурсы.

### Новые ресурсы

| Имя | Тип | Комментарий |
|---|---|---|
| `ExpectedDemand` | Число(15,3) | Ожидаемый спрос за горизонт. |
| `ExpectedRevenue` | Число(15,2) | Ожидаемая выручка. |
| `ExpectedGrossProfit` | Число(15,2) | Ожидаемая валовая прибыль. |
| `ExpectedMarginPercent` | Число(10,2) | Ожидаемая маржа. |
| `Elasticity` | Число(10,4) | Использованная эластичность. |
| `MarketPriceMedian` | Число(15,2) | Медиана рынка. |
| `MarketDemandIndex` | Число(8,4) | Индекс общего спроса. |
| `RelativePriceCurrent` | Число(8,4) | Текущая цена / медиана рынка. |
| `RelativePriceRecommended` | Число(8,4) | Рекомендованная цена / медиана рынка. |

### Новые реквизиты

| Имя | Тип | Комментарий |
|---|---|---|
| `ItemType` | Строка(30) | `product`, `service`, etc. |
| `MarketCategory` | Строка(150) | Рыночная категория. |
| `Region` | Строка(50) | Регион. |
| `Channel` | Строка(50) | Канал. |
| `PriceUnit` | Строка(30) | Единица цены. |
| `MarketContextJSON` | Строка неограниченной длины | Блок `market_context`. |
| `КриваяСпросаJSON` | Строка неограниченной длины | Полный массив `demand_curve`. |
| `OptimizationJSON` | Строка неограниченной длины | Опционально: выбранная точка/constraints. |

---

## 4. Константы

Добавить или переиспользовать константы:

| Имя | Тип | Значение по умолчанию |
|---|---|---|
| `AI_Pricing_DefaultRegion` | Строка(50) | `LV` |
| `AI_Pricing_DefaultChannel` | Строка(50) | `online` |
| `AI_Pricing_DefaultBusinessGoal` | Строка(50) | `maximize_profit` |
| `AI_Pricing_DefaultHorizonDays` | Число(5,0) | `30` |
| `AI_Pricing_MinMarketConfidence` | Число(6,4) | `0.50` |

