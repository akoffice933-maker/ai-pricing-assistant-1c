export const BUSINESS_GOALS = [
  { value: "maximize_profit", label: "Максимизировать прибыль", hint: "цена × спрос − себестоимость → max" },
  { value: "maximize_revenue", label: "Максимизировать выручку", hint: "цена × спрос → max" },
  { value: "grow_market_share", label: "Рост доли рынка", hint: "максимум спроса" },
  { value: "clear_stock", label: "Распродать остаток", hint: "спрос ≈ остаток на складе" },
  { value: "premium_positioning", label: "Премиальное позиционирование", hint: "макс. цена при приемлемом спросе" },
  { value: "maximize_utilization", label: "Загрузка мощностей", hint: "для услуг: спрос ≈ 85% мощности" },
];

export const ITEM_TYPES = [
  { value: "product", label: "Товар" },
  { value: "service", label: "Услуга" },
  { value: "subscription", label: "Подписка" },
  { value: "project", label: "Проект" },
];

export const defaultItem = () => ({
  item_id: "000000123",
  item_type: "product",
  item_name: "Наушники беспроводные X200",
  category: "wireless_headphones",
  current_price: 179.0,
  unit_cost: 128.0,
  price_unit: "unit",
  currency: "EUR",
  sales_last_30_days: 240,
  sales_last_90_days: 620,
  stock_quantity: 180,
  available_capacity: null,
  target_margin_percent: 30,
  quality_index: 1.08,
});

export const defaultMarket = () => ({
  market_category: "wireless_headphones",
  region: "LV",
  channel: "online",
  market_price_median: 189,
  market_demand_index: 1.18,
  promo_share: 0.35,
  availability_index: 0.78,
  seasonality_index: 1.2,
  data_freshness_days: 3,
  coverage_score: 0.78,
  confidence: 0.82,
});

export const defaultConstraints = () => ({
  min_margin_percent: 10,
  max_price_increase_percent: 20,
  max_price_decrease_percent: 30,
  price_ending: 0.99,
  min_confidence_for_apply: 0.7,
});
