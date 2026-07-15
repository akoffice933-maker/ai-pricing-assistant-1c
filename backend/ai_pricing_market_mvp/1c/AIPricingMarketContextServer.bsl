// ОбщийМодуль AIPricingMarketContextServer
// Свойства: Сервер = Истина, ВызовСервера = Ложь.
// Назначение: формирование market_context для FastAPI из регистра AI_РыночныеИндикаторы.

Функция СформироватьMarketContext(Номенклатура, КатегорияРынка = "", Регион = "LV", КаналПродаж = "online", ТипПозиции = "product") Экспорт

    Если КатегорияРынка = "" Тогда
        КатегорияРынка = ОпределитьКатегориюРынка(Номенклатура);
    КонецЕсли;

    Индикаторы = ПолучитьПоследниеРыночныеИндикаторы(КатегорияРынка, Регион, КаналПродаж, ТипПозиции);

    Если Индикаторы = Неопределено Тогда
        // Без market_context новая модель не должна уверенно рекомендовать цену.
        // Но для MVP можно вернуть осторожный fallback.
        Индикаторы = Новый Структура;
        Индикаторы.Вставить("market_price_median", ПолучитьТекущуюЦенуКакFallback(Номенклатура));
        Индикаторы.Вставить("market_demand_index", 1.0);
        Индикаторы.Вставить("promo_share", 0.0);
        Индикаторы.Вставить("availability_index", 1.0);
        Индикаторы.Вставить("seasonality_index", 1.0);
        Индикаторы.Вставить("data_freshness_days", 999);
        Индикаторы.Вставить("confidence", 0.30);
    КонецЕсли;

    MarketContext = Новый Структура;
    MarketContext.Вставить("market_category", КатегорияРынка);
    MarketContext.Вставить("region", Регион);
    MarketContext.Вставить("channel", КаналПродаж);
    MarketContext.Вставить("period", Формат(ТекущаяДата(), "ДФ=yyyy-MM"));

    MarketContext.Вставить("market_price_min", ПолучитьСвойство(Индикаторы, "market_price_min", Неопределено));
    MarketContext.Вставить("market_price_p25", ПолучитьСвойство(Индикаторы, "market_price_p25", Неопределено));
    MarketContext.Вставить("market_price_median", ПолучитьСвойство(Индикаторы, "market_price_median", 0));
    MarketContext.Вставить("market_price_avg", ПолучитьСвойство(Индикаторы, "market_price_avg", Неопределено));
    MarketContext.Вставить("market_price_p75", ПолучитьСвойство(Индикаторы, "market_price_p75", Неопределено));
    MarketContext.Вставить("market_price_max", ПолучитьСвойство(Индикаторы, "market_price_max", Неопределено));

    MarketContext.Вставить("competitor_count", ПолучитьСвойство(Индикаторы, "competitor_count", 0));
    MarketContext.Вставить("active_competitor_count", ПолучитьСвойство(Индикаторы, "active_competitor_count", Неопределено));
    MarketContext.Вставить("market_demand_index", ПолучитьСвойство(Индикаторы, "market_demand_index", 1.0));
    MarketContext.Вставить("search_trend_index", ПолучитьСвойство(Индикаторы, "search_trend_index", Неопределено));
    MarketContext.Вставить("lead_volume_index", ПолучитьСвойство(Индикаторы, "lead_volume_index", Неопределено));
    MarketContext.Вставить("category_views_index", ПолучитьСвойство(Индикаторы, "category_views_index", Неопределено));
    MarketContext.Вставить("promo_share", ПолучитьСвойство(Индикаторы, "promo_share", 0));
    MarketContext.Вставить("availability_index", ПолучитьСвойство(Индикаторы, "availability_index", 1));
    MarketContext.Вставить("seasonality_index", ПолучитьСвойство(Индикаторы, "seasonality_index", 1));
    MarketContext.Вставить("data_freshness_days", ПолучитьСвойство(Индикаторы, "data_freshness_days", 999));
    MarketContext.Вставить("source_count", ПолучитьСвойство(Индикаторы, "source_count", Неопределено));
    MarketContext.Вставить("coverage_score", ПолучитьСвойство(Индикаторы, "coverage_score", 1));
    MarketContext.Вставить("confidence", ПолучитьСвойство(Индикаторы, "confidence", 0.3));

    Возврат MarketContext;

КонецФункции

Функция ПолучитьПоследниеРыночныеИндикаторы(КатегорияРынка, Регион, КаналПродаж, ТипПозиции) Экспорт

    Если Метаданные.РегистрыСведений.Найти("AI_РыночныеИндикаторы") = Неопределено Тогда
        Возврат Неопределено;
    КонецЕсли;

    Запрос = Новый Запрос;
    Запрос.Текст =
    "ВЫБРАТЬ ПЕРВЫЕ 1
    |   Индикаторы.MarketPriceMin КАК market_price_min,
    |   Индикаторы.MarketPriceP25 КАК market_price_p25,
    |   Индикаторы.MarketPriceMedian КАК market_price_median,
    |   Индикаторы.MarketPriceAvg КАК market_price_avg,
    |   Индикаторы.MarketPriceP75 КАК market_price_p75,
    |   Индикаторы.MarketPriceMax КАК market_price_max,
    |   Индикаторы.CompetitorCount КАК competitor_count,
    |   Индикаторы.ActiveCompetitorCount КАК active_competitor_count,
    |   Индикаторы.MarketDemandIndex КАК market_demand_index,
    |   Индикаторы.SearchTrendIndex КАК search_trend_index,
    |   Индикаторы.LeadVolumeIndex КАК lead_volume_index,
    |   Индикаторы.CategoryViewsIndex КАК category_views_index,
    |   Индикаторы.PromoShare КАК promo_share,
    |   Индикаторы.AvailabilityIndex КАК availability_index,
    |   Индикаторы.SeasonalityIndex КАК seasonality_index,
    |   Индикаторы.DataFreshnessDays КАК data_freshness_days,
    |   Индикаторы.SourceCount КАК source_count,
    |   Индикаторы.CoverageScore КАК coverage_score,
    |   Индикаторы.Confidence КАК confidence
    |ИЗ
    |   РегистрСведений.AI_РыночныеИндикаторы КАК Индикаторы
    |ГДЕ
    |   Индикаторы.КатегорияРынка = &КатегорияРынка
    |   И Индикаторы.Регион = &Регион
    |   И Индикаторы.КаналПродаж = &КаналПродаж
    |   И Индикаторы.ТипПозиции = &ТипПозиции
    |УПОРЯДОЧИТЬ ПО
    |   Индикаторы.Период УБЫВ";

    Запрос.УстановитьПараметр("КатегорияРынка", КатегорияРынка);
    Запрос.УстановитьПараметр("Регион", Регион);
    Запрос.УстановитьПараметр("КаналПродаж", КаналПродаж);
    Запрос.УстановитьПараметр("ТипПозиции", ТипПозиции);

    Выборка = Запрос.Выполнить().Выбрать();
    Если Не Выборка.Следующий() Тогда
        Возврат Неопределено;
    КонецЕсли;

    Результат = Новый Структура;
    Результат.Вставить("market_price_min", Выборка.market_price_min);
    Результат.Вставить("market_price_p25", Выборка.market_price_p25);
    Результат.Вставить("market_price_median", Выборка.market_price_median);
    Результат.Вставить("market_price_avg", Выборка.market_price_avg);
    Результат.Вставить("market_price_p75", Выборка.market_price_p75);
    Результат.Вставить("market_price_max", Выборка.market_price_max);
    Результат.Вставить("competitor_count", Выборка.competitor_count);
    Результат.Вставить("active_competitor_count", Выборка.active_competitor_count);
    Результат.Вставить("market_demand_index", Выборка.market_demand_index);
    Результат.Вставить("search_trend_index", Выборка.search_trend_index);
    Результат.Вставить("lead_volume_index", Выборка.lead_volume_index);
    Результат.Вставить("category_views_index", Выборка.category_views_index);
    Результат.Вставить("promo_share", Выборка.promo_share);
    Результат.Вставить("availability_index", Выборка.availability_index);
    Результат.Вставить("seasonality_index", Выборка.seasonality_index);
    Результат.Вставить("data_freshness_days", Выборка.data_freshness_days);
    Результат.Вставить("source_count", Выборка.source_count);
    Результат.Вставить("coverage_score", Выборка.coverage_score);
    Результат.Вставить("confidence", Выборка.confidence);

    Возврат Результат;

КонецФункции

Функция ОпределитьКатегориюРынка(Номенклатура) Экспорт
    // TODO: заменить на маппинг Номенклатура/ВидНоменклатуры/Группа -> market_category.
    Попытка
        Если ЗначениеЗаполнено(Номенклатура.Родитель) Тогда
            Возврат Строка(Номенклатура.Родитель);
        КонецЕсли;
    Исключение
    КонецПопытки;
    Возврат "unknown_market_category";
КонецФункции

Функция ПолучитьТекущуюЦенуКакFallback(Номенклатура)
    // TODO: вызвать ваш AIPricingDataProviderServer.ПолучитьТекущуюЦену(...)
    Возврат 1;
КонецФункции

Функция ПолучитьСвойство(СтруктураДанных, Имя, ЗначениеПоУмолчанию)
    Значение = Неопределено;
    Если СтруктураДанных <> Неопределено И СтруктураДанных.Свойство(Имя, Значение) Тогда
        Если Значение = Null Тогда
            Возврат ЗначениеПоУмолчанию;
        КонецЕсли;
        Возврат Значение;
    КонецЕсли;
    Возврат ЗначениеПоУмолчанию;
КонецФункции
