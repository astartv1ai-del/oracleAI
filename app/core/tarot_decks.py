"""Deck metadata and the canonical 36-card Petit Lenormand catalog.

Deck identity is data, not a prompt instruction: card count, image namespace,
meanings and combination rules travel together with every draw.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

LENORMAND_CARDS = [
    ("rider", "Всадник", "Rider", "весть, движение, прибытие", "весть или импульс"),
    ("clover", "Клевер", "Clover", "малый шанс, лёгкость, удачная возможность", "окно возможности"),
    ("ship", "Корабль", "Ship", "дорога, расстояние, исследование", "движение вдаль"),
    ("house", "Дом", "House", "дом, корни, частная опора", "своя территория"),
    ("tree", "Дерево", "Tree", "рост, здоровье ресурса как образ, корни", "медленный рост"),
    ("clouds", "Облака", "Clouds", "неясность, переменчивая видимость, сомнение", "прояснить оптику"),
    ("snake", "Змея", "Snake", "сложный маршрут, обходной путь, двойственность", "проверить мотивы и путь"),
    ("coffin", "Гроб", "Coffin", "завершение, пауза, закрытие цикла", "положить конец старому"),
    ("bouquet", "Букет", "Bouquet", "подарок, признание, удовольствие", "принять добрый жест"),
    ("scythe", "Коса", "Scythe", "резкий выбор, отсечение, момент решения", "отрезать лишнее осознанно"),
    ("whip", "Метла", "Whip", "повтор, спор, напряжённый ритм", "разорвать повтор"),
    ("birds", "Птицы", "Birds", "разговор, волнение, две точки зрения", "назвать тему разговора"),
    ("child", "Ребёнок", "Child", "начало, любопытство, малая форма", "начать с простого"),
    ("fox", "Лиса", "Fox", "тактика, осторожность, практический ум", "проверить условия"),
    ("bear", "Медведь", "Bear", "ресурс, влияние, защита, крупная сила", "опереться на ресурс"),
    ("stars", "Звёзды", "Stars", "ориентир, надежда, сеть смыслов", "зафиксировать направление"),
    ("stork", "Аист", "Stork", "изменение, переход, обновление", "сделать следующий переход"),
    ("dog", "Собака", "Dog", "дружба, лояльность, надёжная поддержка", "обратиться к союзнику"),
    ("tower", "Башня", "Tower", "дистанция, структура, автономия", "выстроить границу"),
    ("garden", "Сад", "Garden", "сообщество, публичность, встреча", "выйти в подходящую среду"),
    ("mountain", "Гора", "Mountain", "препятствие, медленный маршрут, устойчивость", "разбить препятствие на этапы"),
    ("crossroads", "Развилка", "Crossroads", "альтернативы, выбор, несколько путей", "сравнить последствия"),
    ("mice", "Мыши", "Mice", "утечка ресурса, мелкая тревога, износ", "найти источник утечки"),
    ("heart", "Сердце", "Heart", "привязанность, симпатия, искренний интерес", "назвать ценность"),
    ("ring", "Кольцо", "Ring", "соглашение, обязательство, цикл", "проверить условия договора"),
    ("book", "Книга", "Book", "знание, закрытая информация, обучение", "задать точный вопрос"),
    ("letter", "Письмо", "Letter", "сообщение, документ, письменная фиксация", "зафиксировать словами"),
    ("man", "Мужчина", "Man", "значимая мужская фигура или активная роль", "отделить роль от догадки"),
    ("woman", "Женщина", "Woman", "значимая женская фигура или воспринимающая роль", "отделить роль от догадки"),
    ("lily", "Лилии", "Lily", "зрелость, покой, ценности, чувственность", "выбрать спокойный темп"),
    ("sun", "Солнце", "Sun", "ясность, энергия, видимый результат", "показать результат"),
    ("moon", "Луна", "Moon", "образ, признание, чувствительность, цикл", "отделить образ от факта"),
    ("key", "Ключ", "Key", "доступ, решение, существенная подсказка", "найти главный рычаг"),
    ("fish", "Рыбы", "Fish", "поток, обмен, материальная тема", "проверить поток ресурсов"),
    ("anchor", "Якорь", "Anchor", "устойчивость, работа, длительная опора", "понять, что держит"),
    ("cross", "Крест", "Cross", "ноша, ценность, испытание, принятие смысла", "выбрать посильную ношу"),
]


def lenormand_deck() -> list[dict[str, Any]]:
    return [
        {
            "name": ru,
            "name_en": en,
            "emoji": "◇",
            "meaning": meaning,
            "short": short,
            "advice": advice,
            "arcana": "lenormand",
            "num": str(index),
            "suit": None,
            "img": f"{index:02d}-{slug}",
            "slug": slug,
        }
        for index, (slug, ru, en, meaning, short) in enumerate(LENORMAND_CARDS, 1)
        for advice in [short]
    ]


LEGACY_DECK_ALIASES = {
    "rws-78-v1": "rws-78-geldard-v1",
}


DECK_METADATA: dict[str, dict[str, Any]] = {
    "rws-78-geldard-v1": {
        "deck_id": "rws-78-geldard-v1",
        "label": "Rider–Waite–Smith · Geldard",
        "tradition": "Rider-Waite-Smith",
        "card_count": 78,
        "asset_root": "/static/img/tarot",
        "supports_reversals": True,
        "source_url": "https://commons.wikimedia.org/wiki/Category:Rider-Waite-Smith_tarot_deck_(Geldard)",
        "license_note": "Existing local assets; verify individual Commons file licenses before redistribution.",
        "asset_manifest": "/static/img/tarot/manifest.json",
        "source_verification": "asset_id_complete_individual_provenance_pending",
    },
    "lenormand-36-game-of-hope-v1": {
        "deck_id": "lenormand-36-game-of-hope-v1",
        "label": "Petit Lenormand · Game of Hope",
        "tradition": "Petit Lenormand",
        "card_count": 36,
        "asset_root": "/static/img/lenormand",
        "supports_reversals": False,
        "source_url": "https://commons.wikimedia.org/wiki/File:Das_Spiel_der_Hofnung_(The_Game_of_Hope).png",
        "license_note": "Historical public-domain source as stated on Commons; retain source metadata.",
        "asset_manifest": "/static/img/lenormand/manifest.json",
        "source_verification": "commons_source_reviewed_public_domain_statement",
    },
    "marseille-78-conver-v1": {
        "deck_id": "marseille-78-conver-v1",
        "label": "Tarot de Marseille · historical public-domain reference",
        "tradition": "Tarot de Marseille",
        "card_count": 78,
        "asset_root": "/static/img/marseille",
        "supports_reversals": True,
        "source_url": "https://github.com/mixvlad/TarotCards/tree/main/tarot/marseille",
        "license_note": "Individual Wikimedia Commons public-domain sources are recorded in the asset manifest.",
        "asset_manifest": "/static/img/marseille/manifest.json",
        "source_verification": "per_file_repository_metadata_public_domain_claim",
    },
}


def normalize_deck_id(deck_id: str | None) -> str:
    requested = (deck_id or "rws-78-geldard-v1").strip()
    requested = LEGACY_DECK_ALIASES.get(requested, requested)
    if requested not in DECK_METADATA:
        raise ValueError(f"unknown tarot deck: {deck_id}")
    return requested


def metadata(deck_id: str | None) -> dict[str, Any]:
    return deepcopy(DECK_METADATA[normalize_deck_id(deck_id)])


def cards_for(deck_id: str, rws_cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deck_id = normalize_deck_id(deck_id)
    if deck_id == "lenormand-36-game-of-hope-v1":
        return lenormand_deck()
    # Marseille uses the same canonical 78 identity order but separate assets and
    # interpretation tradition; the adapter marks its deck ID on every card.
    return [dict(card) for card in rws_cards]
