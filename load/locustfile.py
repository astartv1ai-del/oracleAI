"""Locust-сценарий: API Mini App под 50 RPS (SLO из docs/PRODUCTION_READINESS.md §2).

API ходит на сервер, поднятый в DEV_MODE: подписанную Telegram-initData не
шлём, а эмулируем распределение по клиенткам через `?dev_user=», как
умеет `app/api/deps.py` (current_user/rate_limit читают dev_user из query).
dev_user обходит сегмент 100_000_000.. из scripts/seed_load.py, чтобы каждый
виртуальный пользователь попадал на существующую запись и свой rate-limit.

Запуск (~50 RPS: 500 юзеров, 5 новых/с, пауза до 1 с между запросами):

    pip install locust
    DEV_MODE=1 .venv/bin/python -m uvicorn app.main:app --port 8000
    locust -f load/locustfile.py --host http://127.0.0.1:8000 -u 500 -r 5 --run-time 2m

Смотреть p95 (SLO < 400 мс, кроме генераций) в сводке Locust.
"""
from __future__ import annotations

from locust import HttpUser, between, task

BASE_ID = 100_000_000
POOL = 5_000  # столько виртуальных клиенток из сида держим в памяти


def _url(path: str, uid: int) -> str:
    return f"{path}?dev_user={BASE_ID + uid % POOL}"


class MiniAppUser(HttpUser):
    """Читающее поведение Mini App: небольшие GET-запросы, паузы читателя."""

    wait_time = between(0.3, 1.0)

    @task(3)
    def moon_week(self):
        self.client.get(_url("/api/moon/week", self.id))

    @task(2)
    def sky(self):
        self.client.get(_url("/api/sky", self.id))

    @task(2)
    def me(self):
        self.client.get(_url("/api/me", self.id))

    @task(1)
    def diary(self):
        self.client.get(_url("/api/diary", self.id))

    @task(1)
    def horoscope(self):
        # отдельный лимит-бакет "read", у каждого dev_user свои 120/мин
        self.client.get(_url("/api/horoscope", self.id))
