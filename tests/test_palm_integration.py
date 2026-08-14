from __future__ import annotations

import base64
import hashlib
import io
import json
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.api.deps import get_db
from app.api.main import app
from app.core import palm as palm_core
from app.core import skills
from app.core.agents.specs import get
from app.repo import palm as palm_repo, users


FIXTURE = Path(__file__).parent / "fixtures" / "palm" / "palm_hand.jpg"


@pytest.fixture
async def client(db, user):
    app.dependency_overrides[get_db] = lambda: db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    app.dependency_overrides.pop(get_db, None)


def _vision_payload() -> str:
    return json.dumps({
        "status": "complete",
        "image_quality": {"score": 0.93, "issues": []},
        "hand_detected": True,
        "hand_side": "unknown",
        "observations": [
            {"topic": "heart_line", "visibility": "clear",
             "summary": "На фото видна непрерывная дуга под основаниями пальцев.",
             "confidence": 0.84},
            {"topic": "head_line", "visibility": "partial",
             "summary": "Центральный участок линии головы различим, края кадра менее ясны.",
             "confidence": 0.66},
        ],
        "lines": {
            "heart": {"visibility": "clear", "continuity": "continuous", "confidence": 0.84},
            "head": {"visibility": "partial", "confidence": 0.66},
        },
        "mounts": {"venus": {"visibility": "partial", "confidence": 0.55}},
        "fingers": {},
        "interpretive_prompts": ["Где тебе проще показывать чувства действиями, а не словами?"],
        "limitations": ["На одном кадре нельзя уверенно оценить мелкие линии у края ладони."],
        "safety_flags": [],
    }, ensure_ascii=False)


@pytest.mark.asyncio
async def test_real_jpeg_upload_runs_palm_pipeline_and_agent_tools(client, db, user, monkeypatch):
    """Настоящий JPEG проходит HTTP → Pillow → vision boundary → SQLite → tool executor."""
    image = FIXTURE.read_bytes()
    seen: dict[str, object] = {}

    async def fake_complete_vision(system, user_text, image_data_url, **kwargs):
        seen["system"] = system
        seen["user_text"] = user_text
        seen["kwargs"] = kwargs
        assert image_data_url.startswith("data:image/jpeg;base64,")
        encoded = image_data_url.split(",", 1)[1]
        normalized_bytes = base64.b64decode(encoded)
        with Image.open(io.BytesIO(normalized_bytes)) as normalized:
            seen["normalized_size"] = normalized.size
            assert normalized.format == "JPEG"
            assert min(normalized.size) >= palm_core.MIN_SIDE
        return _vision_payload()

    monkeypatch.setattr(palm_core.llm, "complete_vision", fake_complete_vision)

    before = await client.get("/api/palm", params={"dev_user": user["tg_id"]})
    assert before.status_code == 200
    assert before.json() == {"items": [], "raw_image_stored": False}

    response = await client.post(
        "/api/palm",
        params={"dev_user": user["tg_id"]},
        headers={"content-type": "image/jpeg"},
        content=image,
    )
    assert response.status_code == 200, response.text
    result = response.json()
    reading_id = result["id"]
    assert result["status"] == "complete"
    assert result["source"] == "vision_llm_observation"
    assert result["image_meta"]["raw_stored"] is False
    assert result["image_meta"]["width"] == 2592
    assert result["image_meta"]["height"] == 1728
    assert {row["topic"] for row in result["observations"]} == {"heart_line", "head_line"}
    assert seen["normalized_size"] == (2592, 1728)
    assert "видимыми признаками" in str(seen["system"])
    assert seen["kwargs"]["purpose"] == "palm:vision"
    assert seen["kwargs"]["tg_id"] == user["tg_id"]
    response_format = seen["kwargs"]["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    assert response_format["json_schema"]["schema"]["additionalProperties"] is False

    cursor = await db.execute(
        "SELECT id, tg_id, image_sha256, image_size, analysis_json FROM palm_readings WHERE id=?",
        (reading_id,),
    )
    stored = await cursor.fetchone()
    assert stored["id"] == reading_id
    assert stored["tg_id"] == user["tg_id"]
    assert stored["image_sha256"] == hashlib.sha256(image).hexdigest()
    assert stored["image_size"] == len(image)
    assert "heart_line" in stored["analysis_json"]
    assert "image_data" not in stored["analysis_json"]

    listed = await client.get("/api/palm", params={"dev_user": user["tg_id"]})
    assert listed.status_code == 200
    assert listed.json()["items"][0]["id"] == reading_id
    fetched = await client.get(f"/api/palm/{reading_id}", params={"dev_user": user["tg_id"]})
    assert fetched.status_code == 200
    assert fetched.json()["id"] == reading_id

    chiromant = get("chiromant")
    tool_names = {tool["name"] for tool in skills.tools_for(chiromant.skills)}
    assert {"check_palm_quality", "get_palm_map", "get_palm_reading", "get_palm_focus",
            "get_palm_reflection", "compare_palm_readings", "list_palm_readings",
            "request_better_palm_photo"}.issubset(tool_names)
    evidence = await skills.execute(db, user, "get_palm_reading", {"reading_id": reading_id})
    assert "heart_line" in evidence
    assert "vision-наблюдений" in evidence
    focus = await skills.execute(db, user, "get_palm_focus", {"topic": "heart_line"})
    assert '"topic":"heart_line"' in focus
    assert "continuous" in focus
    quality = await skills.execute(db, user, "check_palm_quality", {"reading_id": reading_id})
    assert '"score":0.93' in quality and "raw_image_stored" in quality
    palm_map = await skills.execute(db, user, "get_palm_map", {"reading_id": reading_id})
    assert '"label":"линия сердца"' in palm_map and '"visibility":"partial"' in palm_map
    reflection = await skills.execute(db, user, "get_palm_reflection", {"reading_id": reading_id})
    assert '"questions"' in reflection and "heart_line" in reflection
    second_id = await palm_repo.save_reading(
        db, user["tg_id"], result,
        image_sha256=hashlib.sha256(image + b"-second").hexdigest(),
        image_size=len(image), surface="integration",
    )
    comparison = await skills.execute(db, user, "compare_palm_readings", {
        "current_reading_id": reading_id, "previous_reading_id": second_id,
    })
    assert '"shared_visible_topics"' in comparison and "heart_line" in comparison
    listing = await skills.execute(db, user, "list_palm_readings", {})
    assert f"#{reading_id}" in listing and f"#{second_id}" in listing

    deleted = await client.delete(f"/api/palm/{reading_id}", params={"dev_user": user["tg_id"]})
    assert deleted.status_code == 200
    assert deleted.json() == {"ok": True}
    assert (await client.get(f"/api/palm/{reading_id}", params={"dev_user": user["tg_id"]})).status_code == 404
    deleted_second = await client.delete(f"/api/palm/{second_id}", params={"dev_user": user["tg_id"]})
    assert deleted_second.status_code == 200
    assert "чтений ладони пока нет" in await skills.execute(db, user, "get_palm_reading", {})


@pytest.mark.asyncio
async def test_palm_reading_is_private_and_deleted_from_other_user(client, db, user, monkeypatch):
    """Чтение нельзя получить или удалить по чужому Telegram user id."""
    image = FIXTURE.read_bytes()

    async def fake_complete_vision(*args, **kwargs):
        return _vision_payload()

    monkeypatch.setattr(palm_core.llm, "complete_vision", fake_complete_vision)
    created = await client.post(
        "/api/palm", params={"dev_user": user["tg_id"]},
        headers={"content-type": "image/jpeg"}, content=image,
    )
    reading_id = created.json()["id"]

    await users.ensure(db, 1003, "Другой пользователь")
    other_get = await client.get(f"/api/palm/{reading_id}", params={"dev_user": 1003})
    other_delete = await client.delete(f"/api/palm/{reading_id}", params={"dev_user": 1003})
    assert other_get.status_code == 404
    assert other_delete.status_code == 404

    owner_get = await client.get(f"/api/palm/{reading_id}", params={"dev_user": user["tg_id"]})
    assert owner_get.status_code == 200


@pytest.mark.asyncio
async def test_palm_upload_rejects_invalid_content_and_small_real_image(client, user):
    invalid_type = await client.post(
        "/api/palm", params={"dev_user": user["tg_id"]},
        headers={"content-type": "application/json"}, content=b"{}",
    )
    assert invalid_type.status_code == 415

    invalid_image = await client.post(
        "/api/palm", params={"dev_user": user["tg_id"]},
        headers={"content-type": "image/jpeg"}, content=b"not-an-image",
    )
    assert invalid_image.status_code == 400

    with Image.open(FIXTURE) as source:
        small = source.resize((320, 240))
        buffer = io.BytesIO()
        small.save(buffer, format="JPEG")
    too_small = await client.post(
        "/api/palm", params={"dev_user": user["tg_id"]},
        headers={"content-type": "image/jpeg"}, content=buffer.getvalue(),
    )
    assert too_small.status_code == 400
    assert "минимальная сторона" in too_small.json()["detail"]


@pytest.mark.asyncio
async def test_mira_chat_upload_accepts_png_and_webp(client, user, monkeypatch):
    """Фото из gallery/camera formats проходят тот же backend contract, что и JPEG."""
    async def fake_complete_vision(*args, **kwargs):
        return _vision_payload()

    monkeypatch.setattr(palm_core.llm, "complete_vision", fake_complete_vision)
    with Image.open(FIXTURE) as source:
        original = source.convert("RGB")
        for image_format, mime in (("PNG", "image/png"), ("WEBP", "image/webp")):
            buffer = io.BytesIO()
            original.save(buffer, format=image_format)
            response = await client.post(
                "/api/palm", params={"dev_user": user["tg_id"]},
                headers={"content-type": mime}, content=buffer.getvalue(),
            )
            assert response.status_code == 200, response.text
            result = response.json()
            assert result["status"] == "complete"
            assert result["image_meta"]["raw_stored"] is False
            assert result["image_meta"]["width"] == 2592
            assert result["image_meta"]["height"] == 1728


@pytest.mark.asyncio
async def test_mira_upload_enforces_auth_and_declared_size(client, user):
    no_identity = await client.post("/api/palm", headers={"content-type": "image/jpeg"}, content=b"x")
    assert no_identity.status_code == 401

    unknown = await client.post(
        "/api/palm", params={"dev_user": 987654322},
        headers={"content-type": "image/jpeg"}, content=b"x",
    )
    assert unknown.status_code == 404

    too_large = await client.post(
        "/api/palm", params={"dev_user": user["tg_id"]},
        headers={
            "content-type": "image/jpeg",
            "content-length": str(palm_core.MAX_IMAGE_BYTES + 1),
        }, content=b"x",
    )
    assert too_large.status_code == 413
    assert "8 МБ" in too_large.json()["detail"]
