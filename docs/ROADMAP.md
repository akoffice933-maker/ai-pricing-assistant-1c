# Roadmap

## Stage 0 — Concept

- [x] Разделение ответственности: LLM, skill, 1С.
- [x] ТЗ MVP.

## Stage 1 — Basic AI Pricing Skill

- [x] FastAPI-прототип.
- [x] 1С production skeleton.
- [x] JSON-аудит.
- [x] Черновик документа изменения цен.

## Stage 2 — Market-aware Pricing

- [x] Market Context.
- [x] Demand Curve Skill.
- [x] Price Optimizer.
- [x] Регистр `AI_РыночныеИндикаторы`.
- [x] Загрузчик индикаторов из JSON/CSV.
- [x] Поддержка товаров и услуг.

## Stage 3 — Real Market Data

- [ ] Парсер цен конкурентов.
- [ ] Импорт маркетплейсов.
- [ ] CRM lead volume index для услуг.
- [ ] Расчёт market demand index.
- [ ] Оценка confidence/coverage.

## Stage 4 — ML Elasticity Model

- [ ] История цен + спроса + рынка.
- [ ] Модель эластичности.
- [ ] Backtesting.
- [ ] Контроль прогноза против факта.

## Stage 5 — 1C GraphRAG Adapter

- [ ] Интеграция с анализатором конфигураций 1С.
- [ ] Кросс-доменный граф процедур → метаданные.
- [ ] Автоматический поиск регистров цен/продаж/себестоимости.
- [ ] Автоадаптация data provider под кастомную конфигурацию.

## Stage 6 — Production Pilot

- [ ] Пилот на выбранной группе товаров/услуг.
- [ ] Контроль фактического эффекта 14/30 дней.
- [ ] Отчёт по ROI.
