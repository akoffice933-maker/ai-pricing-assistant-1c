"""Extended coverage tests for AI Pricing Market MVP.

Дополняет test_smoke.py: бизнес-цели оптимизатора, работа ограничений,
расчёт рыночных индикаторов из наблюдений, эластичность, услуги/капасити,
контракт с 1С и форма ошибок валидации.

Run from this directory:
    pip install -r requirements-dev.txt
    pytest -q
"""

import pytest
from fastapi.testclient import TestClient

import main
from main import app
from test_smoke import base_item, base_market

client = TestClient(app)


# ---------------------------------------------------------------------------
# Бизнес-цели оптимизатора
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "goal",
    [
        "maximize_profit",
        "maximize_revenue",
        "grow_market_share",
        "clear_stock",
        "premium_positioning",
        "maximize_utilization",
    ],
)
def test_all_business_goals_return_valid_price(goal):
    item = base_item()
    item["stock_quantity"] = 150
    item["available_capacity"] = 300
    payload = {"business_goal": goal, "item": item, "market_context": base_market()}
    response = client.post("/skills/recommend_price", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["recommended_price"] > 0
    assert data["business_goal"] == goal


def test_premium_positioning_picks_higher_price_than_maximize_revenue():
    item = base_item()
    market = base_market()

    def recommend(goal):
        payload = {"business_goal": goal, "item": item, "market_context": market}
        r = client.post("/skills/recommend_price", json=payload)
        assert r.status_code == 200
        return r.json()["recommended_price"]

    premium_price = recommend("premium_positioning")
    revenue_price = recommend("maximize_revenue")
    assert premium_price >= revenue_price


def test_clear_stock_produces_lower_demand_than_grow_market_share():
    item = base_item()
    item["stock_quantity"] = 50  # заметно ниже базового спроса при текущей цене
    market = base_market()
    # Ослабляем лимит роста цены, иначе таргет по остатку недостижим в рамках дефолтных ограничений.
    constraints = {"max_price_increase_percent": 200.0}

    def demand_for(goal):
        payload = {
            "business_goal": goal,
            "item": item,
            "market_context": market,
            "constraints": constraints,
        }
        r = client.post("/skills/recommend_price", json=payload)
        assert r.status_code == 200
        return r.json()["expected_demand"]

    clear_stock_demand = demand_for("clear_stock")
    grow_share_demand = demand_for("grow_market_share")
    assert clear_stock_demand < grow_share_demand


def test_clear_stock_warns_when_target_unreachable_within_default_constraints():
    item = base_item()
    item["stock_quantity"] = 50  # намного ниже спроса при текущей цене; дефолтный +20% его не даст достичь
    payload = {"business_goal": "clear_stock", "item": item, "market_context": base_market()}
    response = client.post("/skills/recommend_price", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert any("недостижим" in w for w in data["warnings"])


def test_maximize_utilization_targets_85_percent_of_capacity():
    item = base_item(item_type="service", available_capacity=100)
    payload = {"business_goal": "maximize_utilization", "item": item, "market_context": base_market()}
    response = client.post("/skills/recommend_price", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["expected_demand"] <= 100


# ---------------------------------------------------------------------------
# Ограничения (constraints)
# ---------------------------------------------------------------------------


def test_min_margin_percent_is_respected():
    item = base_item(unit_cost=150.0)
    payload = {
        "business_goal": "maximize_revenue",  # тянет цену вниз, маржа — единственный тормоз
        "item": item,
        "market_context": base_market(),
        "constraints": {"min_margin_percent": 40.0},
    }
    response = client.post("/skills/recommend_price", json=payload)
    assert response.status_code == 200
    data = response.json()
    min_allowed_price = 150.0 / (1 - 0.40)
    assert data["recommended_price"] >= min_allowed_price - 0.01


def test_max_price_increase_percent_is_respected():
    item = base_item(current_price=100.0, unit_cost=10.0)
    payload = {
        "business_goal": "premium_positioning",  # тянет цену вверх максимально
        "item": item,
        "market_context": base_market(),
        "constraints": {"max_price_increase_percent": 5.0, "max_price_decrease_percent": 90.0},
    }
    response = client.post("/skills/recommend_price", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["recommended_price"] <= 105.0 + 0.01


def test_max_price_decrease_percent_is_respected():
    item = base_item(current_price=100.0, unit_cost=1.0)
    payload = {
        "business_goal": "clear_stock",
        "item": {**item, "stock_quantity": 1},  # подталкивает к минимальной цене
        "market_context": base_market(),
        "constraints": {"max_price_decrease_percent": 5.0, "max_price_increase_percent": 0.0},
    }
    response = client.post("/skills/recommend_price", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["recommended_price"] >= 95.0 - 0.01


def test_price_ending_rounds_to_expected_fraction():
    item = base_item()
    payload = {
        "business_goal": "maximize_profit",
        "item": item,
        "market_context": base_market(),
        "constraints": {"price_ending": 0.99},
    }
    response = client.post("/skills/recommend_price", json=payload)
    assert response.status_code == 200
    price = response.json()["recommended_price"]
    fractional = round(price - int(price), 2)
    assert fractional in (0.99, 0.0)  # 0.0 допустим, если округление упёрлось в границу


def test_low_confidence_market_requires_manual_approval():
    payload = {
        "business_goal": "maximize_profit",
        "item": base_item(),
        "market_context": base_market() | {"confidence": 0.1},
        "constraints": {"min_confidence_for_apply": 0.9},
    }
    response = client.post("/skills/recommend_price", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["recommended_action"]["requires_approval"] is True


# ---------------------------------------------------------------------------
# Эластичность
# ---------------------------------------------------------------------------


def test_elasticity_override_makes_curve_more_sensitive_to_price():
    item = base_item()
    market = base_market()

    def demand_spread(elasticity_override):
        payload = {"item": item, "market_context": market}
        if elasticity_override is not None:
            payload["elasticity_override"] = elasticity_override
        r = client.post("/skills/forecast_demand_curve", json=payload)
        assert r.status_code == 200
        curve = r.json()["demand_curve"]
        demands = [p["expected_demand"] for p in curve]
        return max(demands) - min(demands)

    mild_spread = demand_spread(-0.5)
    steep_spread = demand_spread(-4.0)
    assert steep_spread > mild_spread


def test_explicit_price_grid_is_respected():
    item = base_item()
    grid = [150.0, 175.0, 200.0, 225.0]
    payload = {"item": item, "market_context": base_market(), "price_grid": grid}
    response = client.post("/skills/forecast_demand_curve", json=payload)
    assert response.status_code == 200
    curve_prices = sorted(p["price"] for p in response.json()["demand_curve"])
    assert curve_prices == sorted(grid)


# ---------------------------------------------------------------------------
# Расчёт рыночных индикаторов из наблюдений
# ---------------------------------------------------------------------------


def _observations():
    return [
        {"price": 170, "competitor_id": "a", "is_promo": False, "is_available": True},
        {"price": 180, "competitor_id": "b", "is_promo": True, "is_available": True},
        {"price": 190, "competitor_id": "c", "is_promo": False, "is_available": False},
        {"price": 200, "competitor_id": "d", "is_promo": False, "is_available": True},
    ]


def test_market_indicators_median_and_percentiles():
    payload = {
        "market_category": "wireless_headphones",
        "region": "LV",
        "channel": "online",
        "observations": _observations(),
    }
    response = client.post("/market/calculate_indicators", json=payload)
    assert response.status_code == 200
    ctx = response.json()["market_context"]
    assert ctx["market_price_min"] == 170
    assert ctx["market_price_max"] == 200
    assert ctx["competitor_count"] == 4
    assert ctx["active_competitor_count"] == 3  # один недоступен


def test_market_indicators_promo_and_availability_shares():
    payload = {
        "market_category": "wireless_headphones",
        "observations": _observations(),
    }
    response = client.post("/market/calculate_indicators", json=payload)
    ctx = response.json()["market_context"]
    assert ctx["promo_share"] == 0.25  # 1 из 4 в промо
    assert ctx["availability_index"] == 0.75  # 3 из 4 доступны


def test_market_indicators_stale_data_reduces_confidence():
    fresh_payload = {
        "market_category": "x",
        "observations": [
            {"price": 100, "competitor_id": "a", "is_promo": False, "is_available": True, "data_freshness_days": 1}
        ],
    }
    stale_payload = {
        "market_category": "x",
        "observations": [
            {"price": 100, "competitor_id": "a", "is_promo": False, "is_available": True, "data_freshness_days": 45}
        ],
    }
    fresh = client.post("/market/calculate_indicators", json=fresh_payload).json()["market_context"]["confidence"]
    stale = client.post("/market/calculate_indicators", json=stale_payload).json()["market_context"]["confidence"]
    assert stale < fresh


def test_market_indicators_export_1c_contains_required_fields():
    payload = {
        "market_category": "wireless_headphones",
        "region": "DE",
        "channel": "retail",
        "observations": _observations(),
    }
    response = client.post("/market/calculate_indicators/export_1c", json=payload)
    assert response.status_code == 200
    record = response.json()[0]
    for field in ("region", "channel"):
        assert field in record, f"'{field}' missing from 1C export record"


# ---------------------------------------------------------------------------
# 1С-контракт в recommend_price
# ---------------------------------------------------------------------------


def test_recommend_price_response_contains_1c_fields():
    item = base_item(price_unit="hour", currency="RUB")
    payload = {"business_goal": "maximize_profit", "item": item, "market_context": base_market()}
    response = client.post("/skills/recommend_price", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["price_unit"] == "hour"
    assert data["currency"] == "RUB"
    assert data["recommended_action"]["document_type"] == "УстановкаЦенНоменклатуры"


# ---------------------------------------------------------------------------
# Форма ошибок валидации
# ---------------------------------------------------------------------------


def test_validation_error_shape():
    payload = {
        "market_category": "x",
        "observations": [],  # нарушает min_length=1
    }
    response = client.post("/market/calculate_indicators", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    assert "errors" in body
    assert isinstance(body["errors"], list)


def test_negative_unit_cost_rejected():
    item = base_item(unit_cost=-1.0)
    payload = {"item": item, "market_context": base_market()}
    response = client.post("/skills/forecast_demand_curve", json=payload)
    assert response.status_code == 422


def test_current_price_must_be_positive():
    item = base_item(current_price=0.0)
    payload = {"item": item, "market_context": base_market()}
    response = client.post("/skills/forecast_demand_curve", json=payload)
    assert response.status_code == 422


def test_market_demand_index_out_of_range_rejected():
    market = base_market()
    market["market_demand_index"] = 10.0  # выше le=5.0
    payload = {"item": base_item(), "market_context": market}
    response = client.post("/skills/forecast_demand_curve", json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Инфраструктура: request_id, model_info
# ---------------------------------------------------------------------------


def test_response_includes_request_id_header():
    response = client.get("/health")
    assert "X-Request-ID" in response.headers


def test_custom_request_id_is_echoed_back():
    response = client.get("/health", headers={"X-Request-ID": "test-req-123"})
    assert response.headers["X-Request-ID"] == "test-req-123"


def test_recommend_price_exposes_price_bounds_and_rejected_points():
    payload = {
        "business_goal": "maximize_profit",
        "item": base_item(),
        "market_context": base_market(),
    }
    response = client.post("/skills/recommend_price", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "price_bounds" in data
    assert data["price_bounds"]["lower_bound"] <= data["price_bounds"]["upper_bound"]
    assert "rejected_points" in data
    assert isinstance(data["rejected_points"], list)


def test_maximize_utilization_warns_when_capacity_is_zero():
    item = base_item(item_type="service", available_capacity=0)
    payload = {"business_goal": "maximize_utilization", "item": item, "market_context": base_market()}
    response = client.post("/skills/recommend_price", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert any("вырождена" in w for w in data["warnings"])


def test_market_context_rejects_inconsistent_percentiles():
    market = base_market()
    market["market_price_min"] = 300  # выше median — несогласовано
    payload = {"item": base_item(), "market_context": market}
    response = client.post("/skills/forecast_demand_curve", json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# /ready — формат CORS origins
# ---------------------------------------------------------------------------


def test_origin_looks_valid_helper():
    assert main._origin_looks_valid("https://example.com") is True
    assert main._origin_looks_valid("http://localhost:5173") is True
    assert main._origin_looks_valid("*") is True
    assert main._origin_looks_valid("example.com") is False  # нет схемы
    assert main._origin_looks_valid("https://example.com/") is False  # лишний слэш
    assert main._origin_looks_valid("https://exa mple.com") is False  # пробел


def test_ready_exposes_allowed_origins_list():
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert "allowed_origins" in data
    assert "cors_origins_look_valid" in data["checks"]


# ---------------------------------------------------------------------------
# Confidence-gating: низкая достоверность или превышение лимита роста цены
# всегда уходят на ручное согласование, а не автоприменение
# ---------------------------------------------------------------------------


def test_low_confidence_forces_manual_review_action():
    payload = {
        "business_goal": "maximize_profit",
        "item": base_item(),
        "market_context": base_market() | {"confidence": 0.2},
        "constraints": {"min_confidence_for_apply": 0.9},
    }
    response = client.post("/skills/recommend_price", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_reliable"] is False
    assert data["recommended_action"]["type"] == "manual_review"
    assert data["recommended_action"]["requires_approval"] is True


def test_recommended_action_always_requires_approval_even_when_reliable():
    payload = {"business_goal": "maximize_profit", "item": base_item(), "market_context": base_market()}
    response = client.post("/skills/recommend_price", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Даже при высоком confidence AI не проводит документ сам — только человек.
    assert data["recommended_action"]["requires_approval"] is True


def test_stale_market_data_lowers_confidence_below_default_threshold():
    stale_market = base_market() | {"data_freshness_days": 60, "coverage_score": 0.2}
    payload = {"business_goal": "maximize_profit", "item": base_item(), "market_context": stale_market}
    response = client.post("/skills/recommend_price", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["confidence"] < base_market()["confidence"]
