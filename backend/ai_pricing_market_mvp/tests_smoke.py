"""Minimal smoke tests for AI Pricing Market MVP.

Run from this directory:
    pip install -r requirements.txt
    pip install pytest
    pytest tests_smoke.py
"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


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


def test_recommend_product_price():
    payload = {
        "business_goal": "maximize_profit",
        "item": {
            "item_id": "000000123",
            "item_type": "product",
            "item_name": "Наушники X200",
            "category": "wireless_headphones",
            "current_price": 179.0,
            "unit_cost": 128.0,
            "sales_last_30_days": 240,
            "sales_last_90_days": 620,
            "quality_index": 1.08,
        },
        "market_context": {
            "market_category": "wireless_headphones",
            "market_price_median": 189,
            "market_demand_index": 1.18,
            "promo_share": 0.35,
            "availability_index": 0.78,
            "seasonality_index": 1.2,
            "data_freshness_days": 3,
            "coverage_score": 0.78,
            "confidence": 0.82,
        },
    }
    response = client.post("/skills/recommend_price", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["recommended_price"] > 0
    assert len(data["demand_curve"]) >= 2
