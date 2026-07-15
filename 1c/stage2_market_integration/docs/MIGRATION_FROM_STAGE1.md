# Миграция с Этапа 1 на Этап 2

## 1. FastAPI

Вместо старого сервиса `ai_skills_1c_prototype` нужно запустить новый:

```bash
cd ai_pricing_market_mvp
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Endpoint остаётся тем же:

```text
POST /skills/recommend_price
```

Но контракт меняется:

```text
было: product + competitor
стало: item + market_context
```

## 2. Метаданные 1С

Добавить:

- `AI_РыночныеИндикаторы`;
- `AI_МаппингРыночныхКатегорий`;
- новые поля в `AI_РекомендацииПоЦенам`.

## 3. Общие модули

Добавить:

- `AIPricingMarketContextServer`;
- `AIPricingMarketIndicatorsLoaderServer`;
- `AIPricingDataProviderMarketServer`;
- `AIPricingRecommendationsMarketServer`;
- `AIPricingStage2TestsServer`.

Старые модули `AIPricingHttpServer`, `AIPricingJSONServer`, `AIPricingDocumentsServer` переиспользуются.

## 4. Старый вызов заменить

Было:

```bsl
AIPricingRecommendationsServer.РассчитатьИЗаписатьРекомендацию(...)
```

Стало:

```bsl
AIPricingRecommendationsMarketServer.РассчитатьИЗаписатьMarketAwareРекомендацию(...)
```

## 5. Хранение аудита

Теперь в `AI_РекомендацииПоЦенам` хранится не только JSON вход/выход, но и:

- `MarketContextJSON`;
- `КриваяСпросаJSON`;
- `OptimizationJSON`.

