# Contributing

Проект пока находится в MVP-стадии.

## Правила

1. Не добавлять реальные клиентские базы 1С.
2. Не добавлять токены, пароли, `.env` и credentials.
3. Для backend изменений проверять:

```bash
cd backend/ai_pricing_market_mvp
python -m py_compile main.py
```

4. Для 1С BSL-кода указывать, под какую конфигурацию адаптирован код: УТ 11, ERP, КА, Розница или кастомная.

## Branch naming

```text
feature/<short-name>
fix/<short-name>
docs/<short-name>
```

## Commit style

```text
feat: add market indicator calculator
fix: correct 1c market context mapping
docs: add pilot plan
```
