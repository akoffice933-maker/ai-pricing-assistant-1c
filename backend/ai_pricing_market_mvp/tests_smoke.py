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


def test_cors_is_not_wildcard_for_arbitrary_origin():
    response = client.get("/health", headers={"Origin": "https://evil.example"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") is None


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


def test_optimize_price_stays_within_bounds_after_rounding():
    payload = {
        "business_goal": "maximize_profit",
        "item": {
            "item_id": "000000001",
            "item_type": "product",
            "item_name": "Boundary Case",
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
            "seasonality_index": 1.0,
            "data_freshness_days": 1,
            "coverage_score": 1.0,
            "confidence": 1.0,
        },
        "demand_curve": [
            {
                "price": 80.0,
                "relative_price": 0.8,
                "value_adjusted_relative_price": 0.8,
                "expected_demand": 10.0,
                "confidence": 0.9,
                "expected_revenue": 800.0,
                "expected_gross_profit": -100.0,
                "margin_percent": 12.5,
                "notes": [],
            }
        ],
    }
    response = client.post("/skills/optimize_price", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["recommended_price"] >= data["constraints"]["lower_bound"]
    assert data["recommended_price"] <= data["constraints"]["upper_bound"]


def test_market_multiplier_does_not_double_count_seasonality():
    from main import DemandCurveRequest, DemandCurveSkill, ItemData, MarketIndicatorsCalculationRequest, MarketObservation, calculate_market_context_from_observations

    market_context = calculate_market_context_from_observations(
        MarketIndicatorsCalculationRequest(
            market_category="test",
            observations=[MarketObservation(price=100.0)],
            seasonality_index=1.2,
        )
    ).market_context

    assert market_context.market_demand_index == 1.2

    skill = DemandCurveSkill()
    item = ItemData(
        item_id="000000002",
        item_name="Seasonality Case",
        category="test",
        current_price=100.0,
        unit_cost=50.0,
        sales_last_30_days=30,
        sales_last_90_days=90,
    )
    response = skill.forecast(DemandCurveRequest(item=item, market_context=market_context, horizon_days=30))
    assert response.diagnostics["market_multiplier"] == 1.2


def test_zero_capacity_is_handled_as_a_real_limit():
    payload = {
        "business_goal": "maximize_utilization",
        "item": {
            "item_id": "000000003",
            "item_type": "service",
            "item_name": "Capacity Case",
            "category": "test",
            "current_price": 100.0,
            "unit_cost": 20.0,
            "available_capacity": 0,
            "sales_last_30_days": 10,
            "sales_last_90_days": 30,
        },
        "market_context": {
            "market_category": "test",
            "market_price_median": 100,
            "market_demand_index": 1.0,
            "seasonality_index": 1.0,
            "data_freshness_days": 1,
            "coverage_score": 1.0,
            "confidence": 1.0,
        },
        "demand_curve": [
            {
                "price": 100.0,
                "relative_price": 1.0,
                "value_adjusted_relative_price": 1.0,
                "expected_demand": 5.0,
                "confidence": 0.9,
                "expected_revenue": 500.0,
                "expected_gross_profit": 400.0,
                "margin_percent": 80.0,
                "notes": [],
            },
            {
                "price": 110.0,
                "relative_price": 1.1,
                "value_adjusted_relative_price": 1.1,
                "expected_demand": 10.0,
                "confidence": 0.9,
                "expected_revenue": 1100.0,
                "expected_gross_profit": 900.0,
                "margin_percent": 81.8,
                "notes": [],
            },
        ],
    }
    response = client.post("/skills/optimize_price", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["selected_point"]["expected_demand"] == 5.0
    assert data["recommended_price"] < 110.0


def test_optimize_price_rejects_empty_demand_curve():
    payload = {
        "business_goal": "maximize_profit",
        "item": {
            "item_id": "000000004",
            "item_type": "product",
            "item_name": "Empty Curve Case",
            "category": "test",
            "current_price": 100.0,
            "unit_cost": 50.0,
        },
        "market_context": {
            "market_category": "test",
            "market_price_median": 100,
            "market_demand_index": 1.0,
        },
        "demand_curve": [],
    }
    response = client.post("/skills/optimize_price", json=payload)
    assert response.status_code == 422
