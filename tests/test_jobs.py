"""Tests for durable background-job state and the authenticated jobs API."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.api.main import app
from app.config import settings
from app.repo import jobs, users
from app.services import jobs as jobs_service


@pytest.fixture
async def client(db):
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.clear()


async def test_task_jobs_status_lifecycle(db, user):
    task_id = "job-lifecycle-1"
    await jobs.create(db, task_id, "llm.chat", tg_id=user["tg_id"],
                      payload={"text": "private prompt", "agent": "oracle"})

    queued = await jobs.get(db, task_id)
    assert queued["status"] == "queued"
    assert queued["payload"] == {"text": "private prompt", "agent": "oracle"}
    assert queued["result"] is None

    await jobs.mark_running(db, task_id)
    running = await jobs.get(db, task_id)
    assert running["status"] == "running"
    assert running["attempts"] == 1
    assert running["started_at"] is not None

    await jobs.mark_retry(db, task_id, "temporary failure", "2099-01-01T00:00:00+00:00")
    retry = await jobs.get(db, task_id)
    assert retry["status"] == "retry"
    assert retry["error"] == "temporary failure"

    await jobs.mark_running(db, task_id)
    await jobs.mark_succeeded(db, task_id, {"answer": "done"})
    succeeded = await jobs.get(db, task_id)
    assert succeeded["status"] == "succeeded"
    assert succeeded["attempts"] == 2
    assert succeeded["result"] == {"answer": "done"}
    assert succeeded["finished_at"] is not None

    await jobs.mark_failed(db, task_id, "late failure must not overwrite success")
    assert (await jobs.get(db, task_id))["status"] == "succeeded"


async def test_jobs_api_rejects_unconfirmed_user_before_enqueue(client, db, user, monkeypatch):
    monkeypatch.setattr(settings, "celery_enabled", True)
    await users.update(db, user["tg_id"], age_confirmed=0)

    response = await client.post(
        "/api/jobs/chat/oracle",
        params={"dev_user": user["tg_id"]},
        json={"text": "queued question"},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "age_confirmation_required"
    cur = await db.execute("SELECT COUNT(*) AS count FROM task_jobs")
    assert (await cur.fetchone())["count"] == 0


async def test_worker_rejects_stale_age_without_calling_chat(db, user, monkeypatch):
    from app.services import chat as chat_service
    from app.tasks import tasks

    task_id = "job-age-revoked-1"
    await jobs.create(db, task_id, "llm.chat", tg_id=user["tg_id"],
                      payload={"text": "private prompt", "agent": "oracle"})
    await users.update(db, user["tg_id"], age_confirmed=0)

    class NonClosingConnection:
        def __getattr__(self, name):
            return getattr(db, name)

        async def close(self):
            return None

    async def fake_connect(*args, **kwargs):
        return NonClosingConnection()

    called = False

    async def forbidden_chat(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("stale queued chat must not reach chat service")

    monkeypatch.setattr(tasks, "connect", fake_connect)
    monkeypatch.setattr(chat_service, "ask", forbidden_chat)

    result = await tasks._chat(
        task_id, user["tg_id"], "private prompt", agent="oracle",
        thread_id=None, allow_paid=False,
    )

    row = await jobs.get(db, task_id)
    assert result == {"status": "rejected", "code": "age_confirmation_required"}
    assert row["status"] == "rejected"
    assert row["result"] is None
    assert row["error"].startswith("age_confirmation_required:")
    assert called is False


async def test_rejected_job_cannot_be_overwritten_by_success(db, user):
    task_id = "job-rejected-terminal-1"
    await jobs.create(db, task_id, "llm.chat", tg_id=user["tg_id"], payload={"agent": "oracle"})
    await jobs.mark_rejected(db, task_id, "age_confirmation_required", "age required")
    await jobs.mark_succeeded(db, task_id, {"answer": "must not persist"})

    row = await jobs.get(db, task_id)
    assert row["status"] == "rejected"
    assert row["result"] is None


async def test_jobs_api_returns_503_when_queue_disabled(client, user, monkeypatch):
    monkeypatch.setattr(settings, "celery_enabled", False)
    response = await client.post("/api/jobs/chat/oracle", params={"dev_user": user["tg_id"]},
                                 json={"text": "queued question"})
    assert response.status_code == 503
    assert response.json()["detail"] == "background queue is disabled"


async def test_jobs_api_validates_agent_before_enqueue(client, user, monkeypatch):
    monkeypatch.setattr(settings, "celery_enabled", True)
    response = await client.post("/api/jobs/chat/not-an-agent",
                                 params={"dev_user": user["tg_id"]},
                                 json={"text": "queued question"})
    assert response.status_code == 404
    assert response.json()["detail"] == "нет такого собеседника"


async def test_jobs_api_enqueue_and_user_scoped_status(client, user, monkeypatch):
    monkeypatch.setattr(settings, "celery_enabled", True)
    sent = []

    def fake_send_task(*args, **kwargs):
        sent.append((args, kwargs))
        return object()

    monkeypatch.setattr(jobs_service.celery_app, "send_task", fake_send_task)
    response = await client.post("/api/jobs/chat/oracle", params={"dev_user": user["tg_id"]},
                                 json={"text": "private prompt"})
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["kind"] == "llm.chat"
    assert len(sent) == 1
    assert sent[0][0] == ("oracle.llm.chat",)
    assert sent[0][1]["args"] == [body["job_id"], user["tg_id"], "private prompt"]

    own = await client.get(f"/api/jobs/{body['job_id']}",
                           params={"dev_user": user["tg_id"]})
    assert own.status_code == 200
    own_body = own.json()
    assert own_body["status"] == "queued"
    assert own_body["result"] is None
    assert "payload" not in own_body
    assert "payload_json" not in own_body

    other = await client.get(f"/api/jobs/{body['job_id']}", params={"dev_user": 1002})
    assert other.status_code == 404

    listing = await client.get("/api/jobs", params={"dev_user": user["tg_id"]})
    assert listing.status_code == 200
    assert listing.json()[0]["id"] == body["job_id"]
    assert "payload" not in listing.json()[0]
