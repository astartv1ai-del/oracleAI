"""Описание LLM-агента и сборка его системного промпта.

Агент — это данные, а не код: имя, образ, набор скиллов, уровень модели. Чтобы
добавить нового агента, достаточно дописать `AgentSpec` в `specs.py` — цикл
tool-use, лимиты, треды и интерфейс уже умеют работать с любым агентом.

Промпт собирается из четырёх слоёв, и порядок важен:
    1. идентичность (кто ты и как говоришь) — кэшируется провайдером;
    2. контекст клиентки (карта, арканы, память) — меняется редко;
    3. правила диалога агента;
    4. правила безопасности — всегда последними, чтобы их не перекрыл образ.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AgentSpec:
    code: str
    name: str                      # имя по умолчанию (у Оракула переопределяется)
    emoji: str
    title: str                     # как называется в интерфейсе
    tagline: str                   # одна строка «зачем он»
    style: str                     # образ и манера речи
    rules: str                     # правила ведения диалога
    skills: tuple[str, ...]
    greeting: str
    accent: str = "#e8c56b"        # цвет ветки чата в Mini App
    tier: str = "main"             # main | lite
    max_tokens: int = 1500
    uses_persona: bool = False     # берёт образ и имя, выбранные клиенткой
    history_limit: int = 14
    suggestions: tuple[str, ...] = field(default_factory=tuple)

    def display_name(self, user=None) -> str:
        if self.uses_persona and user is not None and user["oracle_name"]:
            return user["oracle_name"]
        return self.name

    def as_dict(self, user=None) -> dict:
        return {
            "code": self.code,
            "name": self.display_name(user),
            "emoji": self.emoji,
            "title": self.title,
            "tagline": self.tagline,
            "accent": self.accent,
            "greeting": self.greeting,
            "suggestions": list(self.suggestions),
        }


SAFETY = (
    "Правила безопасности (нерушимые):\n"
    "- Никогда не говори «ты сама виновата», не пугай порчей/сглазом, не осуждай "
    "разводы/аборты/ЛГБТК+, не лезь в религию.\n"
    "- Вопросы здоровья, жизни и смерти: не предсказывай, мягко поддержи и посоветуй "
    "обратиться к врачу/психологу; напомни, что ты — для самопознания.\n"
    "- Не давай финансовых и юридических гарантий, не называй сроки болезни и смерти.\n"
    "- Все расклады и расчёты приходят из инструментов — не выдумывай карты и планеты.\n"
    "- Если клиентка пишет о насилии или мыслях навредить себе: остановись, вырази "
    "поддержку простыми словами и предложи обратиться к живому специалисту."
)

DIALOG_BASE = (
    "Общие правила речи:\n"
    "1. СНАЧАЛА почувствуй её состояние. Если ей больно или тревожно — первой строкой "
    "признай чувство, и только потом переходи к сути.\n"
    "2. Всегда персонально: опирайся на ЕЁ данные и память. Никаких ответов, которые "
    "подошли бы любой.\n"
    "3. Живая речь: короткие абзацы, 1-3 эмодзи, без списков и заголовков — "
    "ты говоришь, а не пишешь доклад.\n"
    "4. Заверши мягким мостиком: короткий вопрос ей или приглашение вернуться."
)


def build_system_prompt(spec: AgentSpec, *, user, agent_name: str,
                        chart_brief: str, matrix_brief: str,
                        memories: list[str], allowance_line: str,
                        style: str | None = None,
                        rules: str | None = None,
                        profile_summary: str = "",
                        extra_rules: str = "") -> str:
    """Собирает системный промпт агента.

    `extra_rules` идёт последним и намеренно: туда попадают предписания
    кризисного протокола (`core/safety.py`), и они должны перекрывать всё
    остальное, включая образ, выбранный клиенткой.
    """
    name = user["name"] or "дорогая"
    mem = "\n".join(f"- {m}" for m in memories) if memories else "- (пока пусто)"
    who = f"Кто она (сводка): {profile_summary}\n\n" if profile_summary else ""
    tail = f"\n\n{extra_rules}" if extra_rules else ""
    return (
        f"Ты — {agent_name}, {spec.title.lower()} в сервисе «Оракул» (Telegram). "
        f"{style or spec.style}\n\n"
        f"Клиентка: {name}.\n"
        f"Её натальная карта: {chart_brief}.\n"
        f"Её Матрица Судьбы: {matrix_brief}.\n\n"
        f"{who}"
        f"Что ты уже знаешь о ней (память):\n{mem}\n\n"
        f"{DIALOG_BASE}\n\n"
        f"{rules or spec.rules}\n\n"
        f"{allowance_line}\n\n"
        f"{SAFETY}{tail}"
    )
