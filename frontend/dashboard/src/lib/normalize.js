export function normalizeItem(item, num) {
  return {
    ...item,
    current_price: num(item.current_price),
    unit_cost: num(item.unit_cost),
    sales_last_30_days: num(item.sales_last_30_days),
    sales_last_90_days: num(item.sales_last_90_days),
    stock_quantity: item.item_type === "product" ? num(item.stock_quantity) : null,
    available_capacity: item.item_type !== "product" ? num(item.available_capacity) : null,
    target_margin_percent: num(item.target_margin_percent),
    quality_index: num(item.quality_index),
  };
}

export function normalizeMarket(market, num) {
  return {
    ...market,
    market_price_median: num(market.market_price_median),
    market_demand_index: num(market.market_demand_index),
    promo_share: num(market.promo_share),
    availability_index: num(market.availability_index),
    seasonality_index: num(market.seasonality_index),
    data_freshness_days: num(market.data_freshness_days),
    coverage_score: num(market.coverage_score),
    confidence: num(market.confidence),
  };
}

export function num(v) {
  return v === "" || v === null || v === undefined ? null : Number(v);
}
