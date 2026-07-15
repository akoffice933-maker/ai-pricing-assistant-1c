#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${BASE_URL:-http://localhost:8000}"
TOKEN_HEADER=()
if [[ -n "${TOKEN:-}" ]]; then
  TOKEN_HEADER=(-H "Authorization: Bearer ${TOKEN}")
fi

echo "Health"
curl -s "${BASE_URL}/health" | python -m json.tool

echo "\nProduct recommendation"
curl -s -X POST "${BASE_URL}/skills/recommend_price" \
  "${TOKEN_HEADER[@]}" \
  -H "Content-Type: application/json" \
  --data @examples/product_recommend_price.json | python -m json.tool

echo "\nService recommendation"
curl -s -X POST "${BASE_URL}/skills/recommend_price" \
  "${TOKEN_HEADER[@]}" \
  -H "Content-Type: application/json" \
  --data @examples/service_recommend_price.json | python -m json.tool


echo "\nCalculate market indicators"
curl -s -X POST "${BASE_URL}/market/calculate_indicators" \
  "${TOKEN_HEADER[@]}" \
  -H "Content-Type: application/json" \
  --data @examples/calculate_market_indicators.json | python -m json.tool
