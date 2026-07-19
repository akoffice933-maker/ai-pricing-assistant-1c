// Реальный ответ /skills/recommend_price на examples/product_recommend_price.json,
// снят живым вызовом backend (не выдуманные числа). Используется для демо-режима,
// когда backend недоступен (например, первый визит на GitHub Pages без локального сервера).
export const DEMO_RESULT = 
{
  "request_id": "product-market-demo-001",
  "item_id": "000000123",
  "item_name": "Наушники беспроводные X200",
  "item_type": "product",
  "price_unit": "unit",
  "currency": "EUR",
  "market_category": "wireless_headphones",
  "business_goal": "maximize_profit",
  "current_price": 179.0,
  "recommended_price": 207.99,
  "price_change_percent": 16.2,
  "expected_demand": 185.19,
  "expected_revenue": 38517.67,
  "expected_gross_profit": 14813.35,
  "expected_margin_percent": 38.46,
  "confidence": 0.6801,
  "is_reliable": false,
  "demand_curve": [
    {
      "price": 143.2,
      "relative_price": 0.7577,
      "value_adjusted_relative_price": 0.7015,
      "expected_demand": 405.21,
      "confidence": 0.6204,
      "expected_revenue": 58025.65,
      "expected_gross_profit": 6159.15,
      "margin_percent": 10.61,
      "notes": [
        "Цена ниже медианы рынка более чем на 10%."
      ]
    },
    {
      "price": 161.1,
      "relative_price": 0.8524,
      "value_adjusted_relative_price": 0.7892,
      "expected_demand": 316.4,
      "confidence": 0.7188,
      "expected_revenue": 50972.39,
      "expected_gross_profit": 10472.91,
      "margin_percent": 20.55,
      "notes": [
        "Цена ниже медианы рынка более чем на 10%."
      ]
    },
    {
      "price": 170.05,
      "relative_price": 0.8997,
      "value_adjusted_relative_price": 0.8331,
      "expected_demand": 282.44,
      "confidence": 0.7691,
      "expected_revenue": 48028.38,
      "expected_gross_profit": 11876.47,
      "margin_percent": 24.73,
      "notes": [
        "Цена ниже медианы рынка более чем на 10%."
      ]
    },
    {
      "price": 170.1,
      "relative_price": 0.9,
      "value_adjusted_relative_price": 0.8333,
      "expected_demand": 282.26,
      "confidence": 0.7694,
      "expected_revenue": 48012.84,
      "expected_gross_profit": 11883.25,
      "margin_percent": 24.75,
      "notes": []
    },
    {
      "price": 179.0,
      "relative_price": 0.9471,
      "value_adjusted_relative_price": 0.8769,
      "expected_demand": 253.59,
      "confidence": 0.82,
      "expected_revenue": 45392.74,
      "expected_gross_profit": 12933.13,
      "margin_percent": 28.49,
      "notes": []
    },
    {
      "price": 187.95,
      "relative_price": 0.9944,
      "value_adjusted_relative_price": 0.9208,
      "expected_demand": 228.89,
      "confidence": 0.7715,
      "expected_revenue": 43020.06,
      "expected_gross_profit": 13722.02,
      "margin_percent": 31.9,
      "notes": []
    },
    {
      "price": 189.0,
      "relative_price": 1.0,
      "value_adjusted_relative_price": 0.9259,
      "expected_demand": 226.23,
      "confidence": 0.7661,
      "expected_revenue": 42757.16,
      "expected_gross_profit": 13799.93,
      "margin_percent": 32.28,
      "notes": []
    },
    {
      "price": 196.9,
      "relative_price": 1.0418,
      "value_adjusted_relative_price": 0.9646,
      "expected_demand": 207.58,
      "confidence": 0.7279,
      "expected_revenue": 40873.38,
      "expected_gross_profit": 14302.57,
      "margin_percent": 34.99,
      "notes": []
    },
    {
      "price": 207.9,
      "relative_price": 1.1,
      "value_adjusted_relative_price": 1.0185,
      "expected_demand": 185.19,
      "confidence": 0.6801,
      "expected_revenue": 38500.2,
      "expected_gross_profit": 14796.37,
      "margin_percent": 38.43,
      "notes": []
    },
    {
      "price": 214.8,
      "relative_price": 1.1365,
      "value_adjusted_relative_price": 1.0523,
      "expected_demand": 172.91,
      "confidence": 0.6529,
      "expected_revenue": 37141.58,
      "expected_gross_profit": 15008.8,
      "margin_percent": 40.41,
      "notes": [
        "Цена выше медианы рынка более чем на 10%."
      ]
    }
  ],
  "elasticity": -2.1003,
  "market_context_summary": {
    "market_category": "wireless_headphones",
    "region": "LV",
    "channel": "online",
    "period": "2026-07",
    "market_price_min": 170.0,
    "market_price_p25": 179.0,
    "market_price_median": 189.0,
    "market_price_avg": 192.0,
    "market_price_p75": 205.0,
    "market_price_max": 229.0,
    "competitor_count": 14,
    "active_competitor_count": 11,
    "market_demand_index": 1.18,
    "search_trend_index": 1.24,
    "category_views_index": 1.15,
    "promo_share": 0.35,
    "availability_index": 0.78,
    "seasonality_index": 1.2,
    "data_freshness_days": 3,
    "source_count": 12,
    "coverage_score": 0.78,
    "confidence": 0.82
  },
  "explanation": {
    "summary": [
      "Выбрана цена 207.99 EUR под цель maximize_profit.",
      "При этой цене ожидаемый спрос за период: 185.19, выручка: 38517.67, валовая прибыль: 14813.35.",
      "Цена находится в допустимом диапазоне 160.00–214.80 с учётом маржи и лимитов изменения.",
      "Цена выше медианы рынка на 10.0%."
    ],
    "positive_factors": [
      "Общий рыночный спрос выше нормы: индекс 1.18.",
      "Позиция имеет премию ценности/качества: индекс 1.08."
    ],
    "negative_factors": [
      "Высокое промо-давление конкурентов: 35% рынка в промо."
    ],
    "neutral_factors": [
      "Текущая цена относительно медианы рынка: 0.947.",
      "Рекомендованная цена относительно медианы рынка: 1.100."
    ]
  },
  "warnings": [],
  "recommended_action": {
    "type": "manual_review",
    "requires_approval": true,
    "document_type": "УстановкаЦенНоменклатуры",
    "valid_for_days": 7,
    "priority": "high"
  },
  "price_bounds": {
    "lower_bound": 160.0,
    "upper_bound": 214.8
  },
  "rejected_points": [
    {
      "price": 143.2,
      "reasons": [
        "ниже нижней границы 160.00"
      ]
    },
    {
      "price": 214.8,
      "reasons": [
        "выше верхней границы 214.80"
      ]
    }
  ],
  "model_version": "demand_curve_v1.0.0-market-relative+price_optimizer_v1.0.0",
  "calculation_timestamp": "2026-07-19T13:21:26.363253+00:00"
};
