# Production-скелет интеграции «AI Pricing Assistant для 1С»

Этот пакет — заготовка для расширения/обработки 1С, которая подключает 1С к FastAPI-сервису `AI Skills Layer` и закрывает production-контур:

1. регистр сведений `AI_РекомендацииПоЦенам`;
2. обработка/расширение 1С с формой рекомендаций;
3. серверные процедуры сбора данных из 1С;
4. создание непроведённого документа `УстановкаЦенНоменклатуры`;
5. сохранение JSON-входа и JSON-выхода для аудита.

## Архитектура

```text
Пользователь 1С
   │
   ▼
Форма AI_РекомендацииПоЦенам
   │
   ▼
AIPricingRecommendationsServer
   │ собирает данные / пишет аудит
   ├──────────────► РегистрСведений.AI_РекомендацииПоЦенам
   │
   ▼
AIPricingHttpServer
   │ HTTP/JSON
   ▼
FastAPI AI Skills Layer
   │
   ▼
ML/Rules skill recommend_price
```

Ключевое правило:

> 1С хранит данные и документы. FastAPI-навык считает. LLM, если используется, только выбирает функцию и объясняет результат. Документы в 1С проводит человек.

## Состав пакета

```text
ai_pricing_1c_integration_skeleton/
├── README.md
├── metadata/
│   ├── METADATA_SPEC.md
│   └── FORM_SPEC.md
├── common_modules/
│   ├── AIPricingSettingsServer.bsl
│   ├── AIPricingJSONServer.bsl
│   ├── AIPricingHttpServer.bsl
│   ├── AIPricingDataProviderServer.bsl
│   ├── AIPricingRecommendationsServer.bsl
│   └── AIPricingDocumentsServer.bsl
├── forms/
│   └── AI_RecommendationsFormModule.bsl
├── examples/
│   ├── extension_installation_checklist.md
│   └── sample_register_record.json
└── docs/
    └── PRODUCTION_NOTES.md
```

## Как использовать

1. Создать расширение 1С, например `AI_Pricing_Assistant`.
2. Добавить объекты метаданных по описанию из `metadata/METADATA_SPEC.md`.
3. Создать общие модули с именами из папки `common_modules` и вставить код.
4. Создать обработку/форму списка рекомендаций по `metadata/FORM_SPEC.md` и вставить код формы из `forms/AI_RecommendationsFormModule.bsl`.
5. Настроить константы подключения к FastAPI-сервису.
6. Адаптировать запросы в `AIPricingDataProviderServer.bsl` под конкретную конфигурацию: УТ 11, ERP, КА, Розница или кастомную базу.
7. Проверить `/health` и `/model_info` FastAPI-сервиса.
8. Запустить расчёт по одному товару.
9. Проверить запись в `AI_РекомендацииПоЦенам`.
10. Проверить создание непроведённого документа `УстановкаЦенНоменклатуры`.

## Предположения скелета

Скелет рассчитан на управляемое приложение 1С 8.3 и типовую торговую архитектуру уровня УТ 11 / ERP / КА.

Некоторые объекты в разных конфигурациях называются по-разному. Поэтому слой `AIPricingDataProviderServer` специально сделан как адаптер. Его нужно довести под конкретную базу.

## Важные production-принципы

- AI не проводит документы.
- Все запросы и ответы сохраняются в аудит.
- Каждая рекомендация имеет `request_id` и `model_version`.
- Рекомендация с низкой надёжностью не должна применяться массово.
- Если товар в акции или цена заблокирована, создаётся только ручной просмотр.
- Документ установки цен создаётся непроведённым.
