# AI Pricing Assistant для 1С

**AI Pricing Assistant для 1С** — прототип market-aware системы ценообразования для 1С, построенный на принципе:

```text
Market Context → Demand Curve → Price Optimization → 1С audit/action
```

Система **не прогнозирует цену напрямую**. Она оценивает общий рынок, строит кривую спроса при разных ценах относительно рынка и выбирает цену под бизнес-цель: прибыль, выручка, доля рынка, распродажа остатков, премиальное позиционирование или загрузка команды.

> LLM не считает цену. LLM может только управлять диалогом, извлекать параметры и вызывать проверяемые навыки. Расчёты выполняет FastAPI Skills Layer, а 1С хранит данные, документы, аудит и решение пользователя.

---

## Ключевая идея

Обычная ошибка pricing-моделей — пытаться предсказать цену напрямую:

```text
факторы → цена
```

В этом проекте используется более корректная схема:

```text
рыночные индикаторы + наша цена относительно рынка → спрос
спрос + ограничения + бизнес-цель → рекомендованная цена
```

Основная формула MVP:

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

---

## Что входит в репозиторий

```text
.
├── backend/
│   └── ai_pricing_market_mvp/              # FastAPI Market-aware Pricing MVP
├── 1c/
│   ├── stage1_integration_skeleton/        # Первый production-скелет интеграции 1С
│   └── stage2_market_integration/          # Этап 2: market_context, demand_curve, рыночные индикаторы
├── docs/
│   ├── TZ_AI_Pricing_Assistant_1C.md       # ТЗ MVP
│   ├── ARCHITECTURE.md                     # Архитектура проекта
│   ├── ROADMAP.md                          # План развития
│   └── GITHUB_DESCRIPTION.md               # Краткое описание для GitHub
└── scripts/
    └── publish_to_github.sh                # Безопасный скрипт публикации через env token
```

---

## Backend: FastAPI Skills Layer

Основной сервис находится здесь:

```text
backend/ai_pricing_market_mvp/
```

### Endpoint'ы

| Endpoint | Назначение |
|---|---|
| `POST /skills/forecast_demand_curve` | Строит кривую спроса `цена → ожидаемый спрос`. |
| `POST /skills/optimize_price` | Выбирает цену по кривой спроса и бизнес-ограничениям. |
| `POST /skills/recommend_price` | Оркестратор: строит кривую спроса и оптимизирует цену одним вызовом. |
| `POST /market/calculate_indicators` | Нормализует сырые наблюдения рынка в `market_context`. |
| `POST /market/calculate_indicators/export_1c` | Возвращает JSON-массив индикаторов для загрузки в 1С. |
| `GET /health` | Liveness-проверка. |
| `GET /ready` | Readiness-проверка (сконфигурирован ли auth/CORS). |

### Быстрый запуск (dev)

```bash
cd backend/ai_pricing_market_mvp
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn main:app --reload --port 8000
```

### Тесты

```bash
cd backend/ai_pricing_market_mvp
pip install -r requirements-dev.txt
pytest -q
```

### Production-запуск

Переменные окружения (см. `.env.example`):

| Переменная | Назначение |
|---|---|
| `ENVIRONMENT` | `production` — сервис откажется стартовать без `AI_PRICING_API_TOKEN`. |
| `AI_PRICING_API_TOKEN` | Bearer-токен для защищённых эндпоинтов. |
| `AI_PRICING_ALLOWED_ORIGINS` | CORS whitelist через запятую (по умолчанию пусто в production). |
| `AI_PRICING_RATE_LIMIT` | Лимит запросов, например `60/minute` (требует `slowapi`). |
| `AI_PRICING_LOG_LEVEL` | Уровень структурированных JSON-логов в stdout. |

```bash
cd backend/ai_pricing_market_mvp
cp ../../.env.example .env   # заполнить реальными значениями
docker compose up --build
```

CI (`.github/workflows/python-check.yml`) на каждый push/PR в `main` гоняет `ruff`, `pytest` и собирает Docker-образ.

Swagger UI:

```text
http://localhost:8000/docs
```

Проверка товара:

```bash
curl -X POST http://localhost:8000/skills/recommend_price \
  -H "Content-Type: application/json" \
  --data @examples/product_recommend_price.json | python -m json.tool
```

Проверка услуги:

```bash
curl -X POST http://localhost:8000/skills/recommend_price \
  -H "Content-Type: application/json" \
  --data @examples/service_recommend_price.json | python -m json.tool
```

---

## 1С-интеграция

### Stage 1

```text
1c/stage1_integration_skeleton/
```

Первый production-скелет:

- регистр `AI_РекомендацииПоЦенам`;
- форма рекомендаций;
- HTTP-вызов FastAPI;
- создание непроведённого документа `УстановкаЦенНоменклатуры`;
- JSON-аудит.

### Stage 2

```text
1c/stage2_market_integration/
```

Market-aware интеграция:

- регистр `AI_РыночныеИндикаторы`;
- регистр `AI_МаппингРыночныхКатегорий`;
- обновление `AI_РекомендацииПоЦенам`;
- хранение `MarketContextJSON`;
- хранение `КриваяСпросаJSON`;
- загрузчик рыночных индикаторов из JSON/CSV;
- поддержка товаров и услуг.

---

## Поддержка товаров и услуг

Для товара система использует:

- текущую цену;
- себестоимость;
- продажи за 30/90 дней;
- остаток;
- рыночную медиану;
- индекс общего спроса;
- промо-давление;
- доступность конкурентов.

Для услуги система использует:

- цену за час/проект/месяц;
- стоимость часа или проекта;
- продажи/часы/сделки;
- доступную мощность;
- загрузку команды;
- рыночную ставку;
- индекс лидов/тендеров;
- supply index специалистов.

---

## Роль LLM

LLM в этой архитектуре не является калькулятором цены.

Она может:

- понять запрос пользователя;
- извлечь параметры;
- выбрать нужный skill;
- вызвать `forecast_demand_curve` или `recommend_price`;
- объяснить результат простым языком.

Она не должна:

- самостоятельно считать цену;
- проводить документы в 1С;
- обходить бизнес-ограничения;
- заменять аудит.

---

## Статус проекта

Текущий статус: **MVP / prototype**.

Готово:

- FastAPI market-aware pricing MVP;
- JSON-контракты;
- примеры товара и услуги;
- 1С production skeleton Stage 1;
- 1С market integration Stage 2;
- регистры и формы в виде BSL/spec;
- приёмочные тесты.

Production-переход требует адаптации под конкретную конфигурацию 1С: УТ 11, ERP, КА, Розница или кастомная база.

---

## Права и лицензия

Public repository, proprietary project.

Код опубликован для демонстрации архитектуры. Использование, копирование, распространение и коммерческое применение требуют отдельного разрешения владельца репозитория.
