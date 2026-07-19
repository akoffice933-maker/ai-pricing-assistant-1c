# Changelog

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/). Версии — не строгий
SemVer от релиза к релизу (тегов пока нет), группировка по содержательным этапам работы.

## [Unreleased]

### Added
- Prometheus `/metrics` — HTTP-трафик (`http_requests_total`,
  `http_request_duration_seconds`) и бизнес-метрики (`price_recommendations_total` по
  business_goal/is_reliable, `price_recommendation_confidence`, `price_recommendation_batch_size`).
- `CHANGELOG.md`, `Makefile`.
- Расширенная feature-таксономия в `docs/MARKET_DATA_METHOD.md` — конкретный список
  признаков (лаги, rolling-статистики, календарь, промо) для будущей обученной модели
  эластичности.

## 2026-07-19 — Дашборд: рыночные индикаторы и сравнение целей
### Added
- Вкладка «Рыночные индикаторы» — калькулятор `market_context` из сырых наблюдений
  конкурентов прямо в браузере.
- Вкладка «Сравнение целей» — параллельный расчёт рекомендации по всем 6 бизнес-целям
  с таблицей и bar-графиком.
- Общий компонент `ItemMarketFields` (вынесен из формы рекомендации, чтобы не дублировать).

## 2026-07-18 — Декомпозиция backend, честная документация ограничений
### Changed
- `main.py` (1256 строк) разбит на пакет `app/` (`config`, `rate_limit`, `security`,
  `utils`, `schemas`, `services/*`, `routers/*`, `server.py`). `main.py` теперь тонкая
  точка входа.
- Переписаны формулировки ограничений модели (`market_demand_index` без реального
  источника данных, эластичность — калиброванная эвристика) — прямая формулировка вместо
  мягкого «production next step», синхронизирована между README, `MARKET_DATA_METHOD.md`
  и `/model_info`.
### Added
- `POST /skills/recommend_price/batch` — пакетный расчёт (до 200 позиций), некорректная
  позиция не роняет весь пакет.
- Версионирование `/v1` — тот же контракт, задублирован с префиксом.
- `scripts/backtest_elasticity.py` — сравнение прогноза кривой спроса с историческими
  данными (пока без реальных данных, только синтетический пример).
- Restyle дашборда под терминальную эстетику (тёмный ink-фон, лайм-акцент, Unbounded/Inter/
  JetBrains Mono).
### Fixed
- `RuntimeError` fail-fast, если `slowapi` не установлен в `ENVIRONMENT=production`
  (раньше — тихое отключение rate limiting).
- Confidence-gating (`is_reliable` → `manual_review`) покрыт тестами.
- Мёртвый `field_validator` для `market_price_max` заменён на реальную кросс-валидацию
  перцентилей.
- `/ready` теперь показывает реальный список `allowed_origins` и проверяет их формат,
  а не просто `bool(ALLOWED_ORIGINS)`.
- Токен дашборда не пишется в `localStorage` для не-localhost backend.

## 2026-07-17 — Веб-дашборд, критический баг с JSON body
### Added
- `frontend/dashboard` — React + Vite + Tailwind + Recharts клиент поверх FastAPI backend.
- Деплой дашборда на GitHub Pages (сначала рядом со статическим preview, затем вместо
  него — statically-served preview убран как избыточный).
### Fixed
- **Критический**: POST-эндпоинты не парсили JSON body на закреплённой версии
  `fastapi==0.115.6` — `from __future__ import annotations` в сочетании с неявным
  `body: Model` параметром ломало распознавание тела запроса. Обнаружено только при
  тестировании в чистом venv по `requirements.txt`, а не в ad-hoc окружении с более
  новой FastAPI.
- `requirements-dev.txt`: `httpx2` требовал более новый `starlette`, чем даёт закреплённая
  `fastapi==0.115.6` — тесты не собирались в чистой установке.
- Добавлен `LICENSE` (proprietary, all-rights-reserved), синхронизирован с текстом в README.

## 2026-07-15 — 2026-07-16 — MVP, ревью-фиксы, production hardening
### Added
- Первая версия FastAPI Skills Layer: Market Context → Demand Curve → Price Optimization.
- 1С Stage 1 (integration skeleton) и Stage 2 (market integration) — BSL-модули, регистры.
- Обязательная Bearer-авторизация в production, structured JSON-логи, CORS whitelist,
  rate limiting (slowapi), global exception handlers, multi-stage Docker.
- Тендерный пакет документов (ТЗ, КП).
### Fixed
- Разделение baseline/forecast рыночного контекста — раньше `market_demand_index`
  не влиял на прогноз из-за самосокращения множителей при калибровке по истории продаж.
- Guardrails оптимизатора (`clamp` по `lower_bound`/`upper_bound`) применяются и в
  fallback-сценарии, и после психологического округления.
- Двойной учёт сезонности и `coverage_score`/freshness в confidence устранён.
