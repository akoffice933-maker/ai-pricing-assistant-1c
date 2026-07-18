"""Тесты на /v1-версионирование и batch-эндпоинт (добавлены при разбивке main.py на пакет app/)."""

from fastapi.testclient import TestClient

from main import app
from test_smoke import base_item, base_market

client = TestClient(app)


# ---------------------------------------------------------------------------
# /v1 — тот же контракт, что и без префикса
# ---------------------------------------------------------------------------


def test_v1_health_matches_bare_health():
    bare = client.get("/health")
    v1 = client.get("/v1/health")
    assert bare.status_code == v1.status_code == 200
    assert bare.json()["service"] == v1.json()["service"]


def test_v1_recommend_price_matches_bare_recommend_price():
    payload = {"business_goal": "maximize_profit", "item": base_item(), "market_context": base_market()}
    bare = client.post("/skills/recommend_price", json=payload)
    v1 = client.post("/v1/skills/recommend_price", json=payload)
    assert bare.status_code == v1.status_code == 200
    assert bare.json()["recommended_price"] == v1.json()["recommended_price"]


def test_v1_market_calculate_indicators_reachable():
    payload = {
        "market_category": "wireless_headphones",
        "observations": [{"price": 100, "competitor_id": "a", "is_promo": False, "is_available": True}],
    }
    response = client.post("/v1/market/calculate_indicators", json=payload)
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Batch
# ---------------------------------------------------------------------------


def _item_payload(**item_overrides):
    item = base_item(**item_overrides)
    return {"business_goal": "maximize_profit", "item": item, "market_context": base_market()}


def test_batch_computes_all_valid_items():
    payload = {"items": [_item_payload(), _item_payload(item_id="000000456")]}
    response = client.post("/skills/recommend_price/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["succeeded"] == 2
    assert data["failed"] == 0
    assert all(r["ok"] for r in data["results"])
    assert all(r["result"]["recommended_price"] > 0 for r in data["results"])


def test_batch_isolates_invalid_item_without_failing_whole_batch():
    payload = {"items": [_item_payload(), {"item": {"item_id": "broken"}}]}
    response = client.post("/skills/recommend_price/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["succeeded"] == 1
    assert data["failed"] == 1
    assert data["results"][0]["ok"] is True
    assert data["results"][1]["ok"] is False
    assert data["results"][1]["error"]


def test_batch_rejects_empty_items_list():
    response = client.post("/skills/recommend_price/batch", json={"items": []})
    assert response.status_code == 422


def test_batch_rejects_more_than_200_items():
    payload = {"items": [_item_payload() for _ in range(201)]}
    response = client.post("/skills/recommend_price/batch", json=payload)
    assert response.status_code == 422


def test_batch_preserves_item_order_via_index():
    payload = {"items": [_item_payload(item_id=f"sku-{i}") for i in range(5)]}
    response = client.post("/skills/recommend_price/batch", json=payload)
    assert response.status_code == 200
    results = response.json()["results"]
    assert [r["index"] for r in results] == [0, 1, 2, 3, 4]
    assert [r["item_id"] for r in results] == [f"sku-{i}" for i in range(5)]
