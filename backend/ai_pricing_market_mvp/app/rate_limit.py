"""Rate limiting (slowapi) — опциональная зависимость с fail-fast в production.

limiter создаётся здесь (не в server.py), чтобы routers могли импортировать
_rate_limit() без цикла server -> routers -> server.
"""

from typing import Callable

from app.config import IS_PRODUCTION, RATE_LIMIT, logger

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address

    _SLOWAPI_AVAILABLE = True
except ImportError:  # pragma: no cover - slowapi is an optional prod dependency
    _SLOWAPI_AVAILABLE = False
    RateLimitExceeded = None  # type: ignore[assignment,misc]
    _rate_limit_exceeded_handler = None  # type: ignore[assignment]

if _SLOWAPI_AVAILABLE:
    limiter = Limiter(key_func=get_remote_address, default_limits=[RATE_LIMIT])
elif IS_PRODUCTION:
    # slowapi зафиксирован в requirements.txt как обязательная зависимость — если его нет
    # в production, это признак сломанной установки, а не осознанного выбора. Как и с
    # токеном, лучше не стартовать вообще, чем молча остаться без rate limiting.
    raise RuntimeError(
        "slowapi не установлен, а ENVIRONMENT=production. Rate limiting обязателен в проде — "
        "проверьте, что requirements.txt установлен полностью (pip install -r requirements.txt)."
    )
else:  # pragma: no cover
    logger.warning(
        "slowapi не установлен — rate limiting отключён (допустимо только вне production). "
        "Добавьте slowapi в requirements.txt для production."
    )
    limiter = None


def _rate_limit(spec: str) -> Callable:
    """No-op decorator when slowapi isn't installed, so routes stay importable."""
    if _SLOWAPI_AVAILABLE:
        return limiter.limit(spec)
    return lambda func: func
