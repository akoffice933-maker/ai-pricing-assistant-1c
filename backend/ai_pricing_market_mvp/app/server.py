"""Сборка FastAPI-приложения: middleware, обработчики ошибок, роутеры.

Роутеры подключены дважды — без префикса (обратная совместимость с текущими
потребителями: дашборд, 1С-примеры, тесты) и под /v1 (версионирование на будущее).
Оба пути ведут в одни и те же функции, дублирования логики нет.
"""

import time
import uuid
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import ALLOWED_ORIGINS, APP_VERSION, SERVICE_NAME, logger
from app.metrics import REQUEST_COUNT, REQUEST_DURATION_SECONDS
from app.rate_limit import _SLOWAPI_AVAILABLE, RateLimitExceeded, _rate_limit_exceeded_handler, limiter
from app.routers import health, market, skills

app = FastAPI(
    title=SERVICE_NAME,
    version=APP_VERSION,
    description=(
        "Market-aware pricing: прогноз кривой спроса относительно рынка и оптимизация цены "
        "под цель бизнеса. LLM не считает цену — она вызывает эти навыки."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or [],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# Сам limiter и fail-fast проверка отсутствия slowapi в production уже выполнены
# при импорте app.rate_limit — здесь только подключаем его к конкретному app.
if _SLOWAPI_AVAILABLE:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next: Callable) -> Response:
    """Присваивает request_id, логирует каждый запрос и время выполнения."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start = time.perf_counter()
    response: Optional[Response] = None
    try:
        response = await call_next(request)
        return response
    finally:
        duration_s = time.perf_counter() - start
        duration_ms = round(duration_s * 1000, 2)
        status_code = response.status_code if response is not None else 500
        logger.info(
            "%s %s status=%s duration_ms=%s request_id=%s",
            request.method,
            request.url.path,
            status_code,
            duration_ms,
            request_id,
        )
        # /metrics сам себя не считает — иначе каждый scrape Prometheus раздувал бы
        # счётчик собственных вызовов.
        if request.url.path != "/metrics":
            REQUEST_COUNT.labels(method=request.method, path=request.url.path, status=status_code).inc()
            REQUEST_DURATION_SECONDS.labels(method=request.method, path=request.url.path).observe(duration_s)
        if response is not None:
            response.headers["X-Request-ID"] = request_id


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    safe_errors = jsonable_encoder(exc.errors(), exclude={"ctx"})
    logger.warning("validation_error path=%s errors=%s", request.url.path, safe_errors)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Некорректные входные данные", "errors": safe_errors},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Не отдаём наружу стектрейс/детали исключения — только в лог сервера.
    logger.exception("unhandled_error path=%s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Внутренняя ошибка сервера"},
    )


# Без префикса — обратная совместимость с текущими потребителями.
app.include_router(health.router)
app.include_router(market.router)
app.include_router(skills.router)

# То же самое под /v1 — на будущее, когда появятся breaking changes в контракте.
app.include_router(health.router, prefix="/v1")
app.include_router(market.router, prefix="/v1")
app.include_router(skills.router, prefix="/v1")
