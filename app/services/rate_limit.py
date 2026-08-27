"""Process-safe and optionally distributed request limiting.

The memory backend is intentionally kept for single-process development. Production
or multi-worker deployments can select ``RATE_LIMIT_BACKEND=redis``. Expensive
buckets fail closed when the shared backend is unavailable unless the operator
explicitly opts into a degraded mode.
"""
from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from ..config import settings


@dataclass(frozen=True)
class LimitDecision:
    allowed: bool
    retry_after: int = 0
    backend: str = "memory"


class MemoryLimiter:
    backend = "memory"

    def __init__(self) -> None:
        self._hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def allow(self, identity: str, bucket: str, limit: int,
                    window: int) -> LimitDecision:
        async with self._lock:
            now = time.monotonic()
            hits = self._hits[(identity, bucket)]
            while hits and now - hits[0] >= window:
                hits.popleft()
            if len(hits) >= limit:
                retry = max(1, int(window - (now - hits[0])))
                return LimitDecision(False, retry, self.backend)
            hits.append(now)
            if len(self._hits) > 50_000:
                self._hits.clear()
            return LimitDecision(True, backend=self.backend)


class RedisLimiter:
    backend = "redis"

    def __init__(self, url: str) -> None:
        from redis.asyncio import Redis

        self._redis = Redis.from_url(url, decode_responses=True)

    async def allow(self, identity: str, bucket: str, limit: int,
                    window: int) -> LimitDecision:
        key = f"oracleai:ratelimit:{bucket}:{identity}"
        pipe = self._redis.pipeline(transaction=True)
        try:
            pipe.incr(key)
            pipe.ttl(key)
            count, ttl = await pipe.execute()
            if count == 1 or ttl < 0:
                await self._redis.expire(key, window)
                ttl = window
            if count > limit:
                return LimitDecision(False, max(1, int(ttl)), self.backend)
            return LimitDecision(True, backend=self.backend)
        finally:
            await pipe.reset()


_limiter = None


def get_limiter():
    global _limiter
    if _limiter is None:
        if settings.rate_limit_backend == "redis":
            try:
                _limiter = RedisLimiter(settings.redis_url)
            except Exception:
                if settings.rate_limit_fail_closed:
                    _limiter = _UnavailableLimiter("redis")
                else:
                    _limiter = MemoryLimiter()
        else:
            _limiter = MemoryLimiter()
    return _limiter


class _UnavailableLimiter:
    def __init__(self, backend: str) -> None:
        self.backend = backend

    async def allow(self, identity: str, bucket: str, limit: int,
                    window: int) -> LimitDecision:
        return LimitDecision(False, window, self.backend)


def reset_limiter_for_tests() -> None:
    global _limiter
    _limiter = None


async def allow(identity: str, bucket: str, limit: int,
                window: int) -> LimitDecision:
    limiter = get_limiter()
    try:
        return await limiter.allow(identity, bucket, limit, window)
    except Exception:
        if settings.rate_limit_fail_closed:
            return LimitDecision(False, window, getattr(limiter, "backend", "unknown"))
        return await MemoryLimiter().allow(identity, bucket, limit, window)
