"""Minimal smoke tests for AI Pricing Market MVP.

Run from this directory:
    pip install -r requirements-dev.txt
    pytest -q
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def base_item():
    return {
        "item_id": "000000123",
        "item_type": "product",
        "item_name": "Наушники X200",
        "category": "wireless_headphones",
        "current_price": 179.0,
        "unit_cost": 128.0,
        "sales_last_30_days": 240,
        "sales_last_90_days": 620,
        "quality_index": 1.08,
    }


def base_market(market_demand_index=1.18):
    return {
        "market_category": "wireless_headphones",
        "region": "LV",
        "channel": "online",
        "market_price_median": 189,
        "market_demand_index": market_demand_index,
        "promo_share": 0.35,
        "availability_index": 0.78,
        "seasonality_index": 1.2,
        "data_freshness_days": 3,
        "coverage_score": 0.78,
        "confidence": 0.82,
    }


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_calculate_market_indicators():
    payload = {
        "market_category": "wireless_headphones",
        "region": "LV",
        "channel": "online",
        "item_type": "product",
        "observations": [
            {"price": 179, "competitor_id": "a", "is_promo": True, "is_available": True},
            {"price": 189, "competitor_id": "b", "is_promo": False, "is_available": True},
            {"price": 205, "competitor_id": "c", "is_promo": False, "is_available": False},
        ],
    }
    response = client.post("/market/calculate_indicators", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["market_context"]["market_price_median"] == 189
    assert data["market_context"]["competitor_count"] == 3
    assert data["one_c_indicator_record"]["market_category"] == "wireless_headphones"


def test_calculate_market_indicators_export_1c():
    payload = {
        "market_category": "wireless_headphones",
        "observations": [
            {"price": 179},
            {"price": 189},
            {"price": 205},
        ],
    }
    response = client.post("/market/calculate_indicators/export_1c", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["market_price_median"] == 189


def test_recommend_product_price():
    payload = {
        "business_goal": "maximize_profit",
        "item": base_item(),
        "market_context": base_market(),
    }
    response = client.post("/skills/recommend_price", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["recommended_price"] > 0
    assert data["price_unit"] == "unit"
    assert data["currency"] == "EUR"
    assert data["market_context_summary"]["region"] == "LV"
    assert len(data["demand_curve"]) >= 2


def test_market_demand_index_changes_curve():
    low = {
        "item": base_item(),
        "market_context": base_market(market_demand_index=0.80),
        "price_grid": [179, 189],
    }
    high = {
        "item": base_item(),
        "market_context": base_market(market_demand_index=1.20),
        "price_grid": [179, 189],
    }
    low_response = client.post("/skills/forecast_demand_curve", json=low)
    high_response = client.post("/skills/forecast_demand_curve", json=high)
    assert low_response.status_code == 200
    assert high_response.status_code == 200
    low_demand = low_response.json()["demand_curve"][0]["expected_demand"]
    high_demand = high_response.json()["demand_curve"][0]["expected_demand"]
    assert high_demand > low_demand


def test_optimizer_never_violates_min_margin_after_fallback_and_rounding():
    payload = {
        "business_goal": "maximize_profit",
        "item": {
            "item_id": "x",
            "item_type": "product",
            "item_name": "Margin constrained item",
            "category": "test",
            "current_price": 100.0,
            "unit_cost": 90.0,
            "sales_last_30_days": 10,
            "sales_last_90_days": 30,
        },
        "market_context": {
            "market_category": "test",
            "market_price_median": 100,
            "market_demand_index": 1.0,
        },
        "price_grid": [80, 100],
        "constraints": {
            "min_margin_percent": 30,
            "max_price_increase_percent": 10,
            "max_price_decrease_percent": 30,
            "price_ending": 0.99,
            "min_confidence_for_apply": 0.1,
        },
    }
    response = client.post("/skills/recommend_price", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["recommended_price"] >= 90 / (1 - 0.30) - 0.01
    assert data["expected_margin_percent"] >= 30 - 0.01
