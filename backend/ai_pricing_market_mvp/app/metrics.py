"""Prometheus-метрики.

/metrics отдаётся без авторизации (как /health, /ready) — Prometheus-скрейпер обычно не
шлёт Bearer-токен. В production эндпоинт стоит закрыть на уровне сети (firewall/internal-only
route в reverse proxy), а не полагаться на app-level auth — см. README.
"""

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Общее число HTTP-запросов",
    ["method", "path", "status"],
)

REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Время обработки запроса, секунды",
    ["method", "path"],
)

RECOMMENDATIONS_TOTAL = Counter(
    "price_recommendations_total",
    "Число рассчитанных рекомендаций по цене",
    ["business_goal", "is_reliable"],
)

RECOMMENDATION_CONFIDENCE = Histogram(
    "price_recommendation_confidence",
    "Распределение confidence по рекомендациям (0..1)",
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)

BATCH_SIZE = Histogram(
    "price_recommendation_batch_size",
    "Размер пакетных запросов /skills/recommend_price/batch",
    buckets=(1, 5, 10, 25, 50, 100, 200),
)


def render_latest() -> tuple[bytes, str]:
    """Возвращает (тело, content-type) для эндпоинта /metrics."""
    return generate_latest(), CONTENT_TYPE_LATEST
