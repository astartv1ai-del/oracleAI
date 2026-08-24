from __future__ import annotations

from app.core.agents.file_loader import (
    load_profiles,
    profile_for_legacy,
    select_skills,
    skill_context,
)
from app.core.agents.specs import codes, get


def test_file_profiles_and_skills_are_discovered():
    profiles = load_profiles()
    assert set(profiles) == {"lilith", "urania", "lenormand", "mira"}
    assert all(len(item.skills) >= 20 for item in profiles.values())


def test_skill_frontmatter_is_portable_and_unique():
    profiles = load_profiles()
    for profile in profiles.values():
        for skill in profile.skills:
            assert skill.name == skill.path.rsplit("/", 2)[-2]
            assert skill.description
            assert skill.metadata["oracleai_agent"] == profile.agent_id
            assert skill.metadata.get("oracleai_loading", "on_demand") == "on_demand"
        assert profile.handbook


def test_russian_queries_select_relevant_specialist_skill():
    mira = profile_for_legacy("chiromant")
    urania = profile_for_legacy("astro")
    tarot = profile_for_legacy("tarot")
    assert mira is not None and urania is not None and tarot is not None
    assert select_skills(mira, "фото ладони", 1)[0].name == "palm-photo-quality"
    assert select_skills(mira, "линия сердца", 1)[0].name == "heart-line"
    assert select_skills(urania, "транзиты планет", 1)[0].name == "transits"
    assert select_skills(tarot, "расклад таро", 1)[0].name == "three-card-spread"


def test_skill_context_is_bounded_and_legacy_registry_is_unchanged():
    context = skill_context("chiromant", "фото ладони и линия сердца", limit=3)
    assert context.count("ACTIVE_SKILL:") <= 3
    assert "DOMAIN_PLAYBOOK" in context
    assert len(context) < 24000
    assert codes() == ("oracle", "astro", "tarot", "chiromant")
    assert get("chiromant").skills == (
        "palm_scanner",
        "palm_photo_guide",
        "palm_history",
    )


async def test_runtime_places_active_skills_before_safety_tail(monkeypatch):
    from app.core.agents import runtime

    spec = get("astro")
    user = {"lang": "ru", "name": "Тест", "gender": None, "memory_enabled": False}
    user["oracle_name"] = None

    async def fake_resolve(db, code):
        return spec, spec.style, spec.rules

    async def fake_context(db, current_user, current_spec, question=""):
        return "chart", "matrix", [], ""

    monkeypatch.setattr(runtime, "resolve", fake_resolve)
    monkeypatch.setattr(runtime, "_context", fake_context)
    prompt = await runtime.system_for(None, user, spec, question="транзиты планет")
    assert "ACTIVE_SKILL: anti-barnum-protocol" in prompt
    assert prompt.index("ACTIVE_SKILL:") < prompt.index("Правила безопасности")
