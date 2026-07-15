# Installation guide

## 1. Backend

```bash
cd backend/ai_pricing_market_mvp
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Проверка:

```bash
curl http://localhost:8000/health
```

## 2. Расчёт market indicators из сырого CSV

```bash
python scripts/calculate_market_indicators.py \
  --input docs/examples/raw_market_observations.csv \
  --output docs/examples/calculated_market_indicators.json
```

Полученный JSON можно загрузить в 1С через форму `AI_MarketIndicatorsLoader`.

## 3. 1С Stage 2

В расширение 1С добавить:

1. регистр `AI_РыночныеИндикаторы`;
2. регистр `AI_МаппингРыночныхКатегорий`;
3. новые поля в `AI_РекомендацииПоЦенам`;
4. общие модули из `1c/stage2_market_integration/common_modules`;
5. формы из `1c/stage2_market_integration/forms`.

## 4. Настройки 1С

```text
AI_Pricing_Host = localhost
AI_Pricing_Port = 8000
AI_Pricing_UseHTTPS = Ложь
AI_Pricing_DefaultBusinessGoal = maximize_profit
AI_Pricing_DefaultHorizonDays = 30
```

## 5. Smoke test

1. Загрузить рыночные индикаторы.
2. Создать маппинг категории.
3. Рассчитать рекомендацию.
4. Проверить `JSONВход`, `JSONВыход`, `КриваяСпросаJSON`.
5. Создать непроведённый документ изменения цен.
