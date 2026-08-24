"""Скиллы — инструменты, которые LLM вызывает через tool-use.

Каждый скилл состоит из трёх частей:
- `schema` — описание для модели (что это и когда звать);
- `run(db, user, args) -> str` — детерминированное исполнение: считает КОД;
- guide — правила трактовки, которые подмешиваются в результат, чтобы модель
  разбирала данные по правилам школы, а не как получится.

Ключевой инвариант продукта: модель никогда не выдумывает карты, планеты и
арканы — она получает готовый расчёт и объясняет его. Отсюда и «правдивость»,
на которой держится доверие к сервису.

Правила трактовки берутся из БД (`content_items(kind='guide')`), а константы в
этом файле — значение по умолчанию. Так тексты правятся в админке без деплоя, но
пустая база или сбой запроса не ломают ответ.
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta

from ..repo import content as content_repo
from ..repo import dialog as dialog_repo
from ..repo import readings as readings_repo
from ..repo import palm as palm_repo
from . import astro, memory, palm, placements, tarot, vedic
from .matrix import compute_matrix, matrix_brief

log = logging.getLogger("oracle.skills")

# ---------------------------------------------------------------- guides

TAROT_GUIDE = (
    "[Правила трактовки Таро — школа Райдера-Уэйта-Смит (RWS)]\n"
    "1) Колода символическая (А.Уэйт + Памела Колман Смит, 1909): смысл несёт картина — "
    "фигуры, жесты, цвета, сюжет. Смотри на образ карты и символы, а не на словарь значений.\n"
    "2) Родной порядок старших: Сила — VIII, Правосудие — XI (НЕ наоборот, как в Марселе).\n"
    "3) Старший аркан = архетип-веха (Шут-начало, Маг-воля, Жрица-интуиция, Императрица-"
    "изобилие, Император-порядок, Иерофант-традиция, Влюблённые-выбор, Колесница-воля/победа, "
    "Сила-кротость, Отшельник-поиск, Колесо-циклы, Правосудие-равновесие, Повешенный-пауза/взгляд, "
    "Смерть-трансформация, Умеренность-алхимия, Дьявол-зависимость, Башня-прорыв, Звезда-надежда, "
    "Луна-страхи/подсознание, Солнце-радость/ясность, Суд-призвание, Мир-целостность). "
    "Тревожные арканы объясняй ресурсом (Смерть=завершение, Башня=слом старого ради правды, "
    "Дьявол=что можно отпустить), а не пугая.\n"
    "4) Младшие: масти = стихии и сферы — Жезлы=огонь/дело, Кубки=вода/чувства, Мечи=воздух/"
    "мысли, Пентакли=земля/деньги/тело. Числа 1-10 = прогрессия (Туз=потенциал, 2=выбор, "
    "3=рост, 4=стабильность, 5=кризис, 6=гармония, 7=испытание, 8=движение, 9=почти итог, "
    "10=завершение цикла): значение = число × сфера масти. Двор = люди/роли: Паж=вестник/ученик, "
    "Рыцарь=порыв/действие, Королева=зрелая внутренняя энергия, Король=мастерство/воля.\n"
    "5) Перевёрнутая — НЕ «плохо» и НЕ «смысл наоборот»: по Грир это энергия заблокированная "
    "или смещённая внутрь (не прожита, спрятана), задержанная во времени, или теневая сторона "
    "архетипа (та же Сила — но робость). Вопрос: «какая часть этой карты сейчас ей недоступна "
    "и что ей нужно?».\n"
    "6) Связывай карты в один сюжет по позициям расклада: что причина, что следствие, где поворот. "
    "Паттерны: перевес одной масти = ведущая сфера, повторы чисел = сквозная тема, старшие = главные "
    "вехи.\n"
    "7) Обязательно: ТОЛЬКО выпавшие карты, ответ на ЕЁ вопрос + 1 конкретный мягкий совет в конце. "
    "Говори вероятностно («карта может указывать на…»), без фатализма: выбор всегда за ней."
)

NATAL_GUIDE = (
    "[Натальная астрология — как читает профи]\n"
    "1) Четыре пласта, всегда в этом порядке: планета 'что', знак 'как', дом 'где в жизни', "
    "аспект 'как это стыкуется с остальным'. Один факт сам по себе нем — силу даёт связка.\n"
    "2) Костяк личности читай по тройке: Солнце (воля и роль), Луна (душа и как ей себя "
    "успокоить), Асцендент (как её видит мир и первое впечатление). MC — куда карабкается "
    "по жизни.\n"
    "3) Акценты карты (в данных) — это темы жизни: перевес стихии = чем она 'дышит', "
    "стеллиум = сгусток силы в одной сфере, угловая планета у ASC/MC = главный козырь и "
    "одновременно главный вызов.\n"
    "4) Венера и Марс — её любовный профиль: Венера чего ждёт и ценит, Марс как добивается "
    "и чего хочет. Луна в знаке — эмоциональная природа (не критикуй её — объясни).\n"
    "5) Ретро-планеты — энергия, работающая внутрь: у неё там не слабость, а свой ритм "
    "созревания. Не называй это 'задержкой'.\n"
    "6) Не пугай: Сатурн — учитель и границы, Плутон — трансформация, Раху (северный узел) — "
    "куда расти в жизни, Кету — что уже умеет и от чего устало. Говори ресурсом, не приговором.\n"
    "7) Обязательно привязывай к ЕЁ жизни из памяти (профессия, люди, чувства), слово "
    "'у тебя' вместо 'у этого знака'. И главное: если время рождения неточное — дома и "
    "асцендент НЕ трогай, читай только по знакам и стихиям.\n"
    "8) Порядок работы: сначала вспомни клиентку (сводка и факты из памяти — кто она, "
    "что у неё сейчас в жизни), потом считай и трактуй карту под НЕЁ, а не абстрактно."
)

TRANSIT_GUIDE = (
    "[Прогнозы — как делает профи]\n"
    "1) Прогноз всегда с двух ног: фон неба (фаза Луны, лунный день, сезон Солнца, где сейчас "
    "Луна и Венера) + её точка опоры (её Солнце, а из памяти — что у неё сейчас в жизни).\n"
    "2) Формула ответа: настроение дня + 1 сфера внимания + 1 конкретный совет на сегодня. "
    "Никаких простыней 'страшилок' на весь гороскоп.\n"
    "3) Лунная фаза диктует тактику: новолуние — сеять намерения, растущая — действовать и "
    "просить, полнолуние — эмоции громче логики, не решать судьбоносно, убывающая — "
    "завершать и благодарить.\n"
    "4) Рост/убывание Луны и её знак — в данных: трактуй знак как 'каким тоном сегодня "
    "чувствуется мир' (Луна в водном — прислушиваться к себе, в огненном — инициатива).\n"
    "5) Говори вероятностно и бережно: не предсказывай беды, болезни и смерти. Если видишь "
    "напряжённый день — предложи, как пройти его мягче, а не пугай."
)

MATRIX_GUIDE = (
    "[Правила Матрицы Судьбы]\n"
    "1) Аркан — это энергия с плюсом и минусом: покажи оба полюса и как выйти в плюс. "
    "2) Аркан судьбы — главный вектор, центр — зона комфорта. 3) Говори про ресурс, а не приговор."
)

COMPAT_GUIDE = (
    "[Совместимость — как разбирает профи]\n"
    "1) Читай пару на трёх уровнях, как есть в данных: стихии Солнц (общий климат), "
    "Луна и Венера обоих (душа и любовь), крест Солнце-Луна (самая живая нить — "
    "друг греет её душу или его вода тушит её огонь), а при полных картах — синастрические "
    "аспекты пары.\n"
    "2) Стихии: огонь+воздух и земля+вода питают друг друга — им легко; огонь+земля и "
    "огонь+вода — рост через трение; говори про это как «у вас разный язык», а не брак "
    "в небесах.\n"
    "3) Аспекты пары: трины и секстили — что даётся без усилий (их козырь), квадраты и "
    "оппозиции — где ранит и чему придётся учиться (их работа). Не называй аспект "
    "приговором — объясни, как его прожить.\n"
    "4) Живи по сферам разбора (любовь, быт, дело, дружба, рост): по каждой скажи, что "
    "связывает, где трение и что укрепит именно её. Так разбор про отношения, а не про "
    "одну цифру.\n"
    "5) Балл — РОВНО то число из данных (его видно на шкале), ориентир, а не вердикт. "
    "Никогда не пиши «вы несовместимы» — покажи, ЧТО укрепит союз, и оставь выбор за ней. "
    "Тепло, живо, без канцелярита.\n"
    "6) Порядок работы: сначала вспомни клиентку и их пару (кто они, что между ними "
    "из памяти), потом разбирай совместимость под их конкретику."
)

DIARY_GUIDE = (
    "[Правила работы с дневником]\n"
    "1) Опирайся на её собственные слова из записей — цитируй коротко. "
    "2) Отмечай динамику («три недели назад ты писала иначе»). "
    "3) Не оценивай и не поучай: отражай и поддерживай."
)

CAREER_GUIDE = (
    "[Карьера — как разбирает профи]\n"
    "1) Направление читай связкой, а не одной планетой: MC и его управитель (куда зовёт "
    "вершина), Сатурн (через что растёт и где дисциплина), Солнце (что зажигает), аркан "
    "судьбы из Матрицы. Стихия сильного перевеса подсказывает среду: огонь — старты и "
    "лидерство, земля — ресурсы и структуры, воздух — люди и идеи, вода — забота и глубина.\n"
    "2) Не вешай профессию как ярлык — опиши РОЛЬ, среду и условия, в которых ей хорошо "
    "(темп, самостоятельность, люди), и оставь конкретику за ней.\n"
    "3) Тайминги — ТОЛЬКО из деловых окон по Луне в данных, дат не выдумывай: растущая — "
    "начинать и просить, убывающая — закрывать и увольняться, полнолуние — не подписывать "
    "и не ссориться, новолуние — планировать.\n"
    "4) Про руководство и коллег — через стихии и потребности: «ей нужен каркас и "
    "предсказуемость» вместо «начальник-Козерог вас задавит».\n"
    "5) Деньги и должности не обещай и не гарантируй: говори о её ресурсе, сильных "
    "сторонах и цене, которую она имеет право называть."
)

PRACTICE_GUIDE = (
    "[Правила работы с практиками]\n"
    "1) Практика — это дисциплина, а не магия: подчёркивай непрерывность дней. "
    "2) Никогда не обещай результата к сроку и не пугай последствиями пропуска. "
    "3) Опирайся на «знаки продвижения» из описания практики — они помогают "
    "заметить эффект и не бросить. 4) Если её запрос про здоровье или тяжёлое "
    "состояние — практику не назначай, направь к специалисту."
)

DEFAULT_GUIDES = {
    "tarot": TAROT_GUIDE, "natal": NATAL_GUIDE, "transit": TRANSIT_GUIDE,
    "matrix": MATRIX_GUIDE, "compat": COMPAT_GUIDE, "diary": DIARY_GUIDE,
    "career": CAREER_GUIDE, "practice": PRACTICE_GUIDE,
}


async def guide(db, code: str) -> str:
    """Правила трактовки: из БД, иначе встроенные."""
    default = DEFAULT_GUIDES.get(code, "")
    if db is None:
        return default
    try:
        return await content_repo.get_text(db, "guide", code, default) or default
    except Exception as e:  # noqa: BLE001
        log.warning("правила %s из БД недоступны: %s", code, e)
        return default


# ---------------------------------------------------------------- helpers

ELEMENT_SCORE = {
    frozenset(["огонь"]): 88, frozenset(["земля"]): 86,
    frozenset(["воздух"]): 85, frozenset(["вода"]): 90,
    frozenset(["огонь", "воздух"]): 84, frozenset(["земля", "вода"]): 87,
    frozenset(["огонь", "земля"]): 58, frozenset(["огонь", "вода"]): 52,
    frozenset(["воздух", "земля"]): 56, frozenset(["воздух", "вода"]): 63,
}

# Вклады в балл пары. Балл должен объясняться, а не выглядеть магией.
ASPECT_BONUS = {"trine": 6, "sextile": 4, "conjunction": 3,
                "square": -4, "opposition": -3}


def synastry_bonus(aspects: list[dict]) -> int:
    """Суммарный вклад синастрических аспектов в балл пары."""
    return sum(ASPECT_BONUS.get(a.get("code", ""), 0) for a in aspects)


def _element_bonus(a: str | None, b: str | None) -> int:
    """Созвучие двух стихий: +4 созвучные, -3 в трении, 0 нейтрально."""
    if not a or not b:
        return 0
    if a == b:
        return 4
    if frozenset((a, b)) in (frozenset(["огонь", "воздух"]),
                             frozenset(["земля", "вода"])):
        return 4
    if frozenset((a, b)) in (frozenset(["огонь", "земля"]),
                             frozenset(["огонь", "вода"])):
        return -3
    return 0  # воздух-земля и воздух-вода — нейтрально: не питают и не режут


# Спидометр v2: балл пары разворачивается в сферы жизни. Каждая — комбинация
# одних и тех же данных (стихии/Луна/Венера/крест) с разным акцентом, а итог —
# их взвешенное среднее по типу связи. Slugs стабильны: их знает Mini App.
_SPHERE_ORDER = ("love", "harmony", "career", "friendship", "growth")
_SPHERE_DEFS = {
    "love": "Любовь и страсть", "harmony": "Быт и уют",
    "career": "Работа и дела", "friendship": "Дружба и доверие",
    "growth": "Вместе расти",
}
_RELATION_LABEL = {
    "love": "любовная пара", "friend": "друзья и подруги",
    "work": "коллеги", "family": "родные",
}


def relation_label(relation: str) -> str:
    """Публичная подпись типа связи для интерфейсных адаптеров."""
    return _RELATION_LABEL.get(relation, "")


# Вес сферы зависит от того, кем люди друг другу приходятся.
_RELATION_WEIGHTS = {
    "love":   {"love": 0.40, "harmony": 0.20, "career": 0.10,
               "friendship": 0.15, "growth": 0.15},
    "friend": {"love": 0.10, "harmony": 0.15, "career": 0.20,
               "friendship": 0.35, "growth": 0.20},
    "work":   {"love": 0.10, "harmony": 0.15, "career": 0.40,
               "friendship": 0.15, "growth": 0.20},
    "family": {"love": 0.25, "harmony": 0.30, "career": 0.15,
               "friendship": 0.15, "growth": 0.15},
}
RELATIONS = frozenset(_RELATION_WEIGHTS)


# В какой сфере живёт стихия. Огонь — страсть, земля — быт, воздух — дружба,
# вода — чувства/рост. Офсет сферы = (вклад стихий обоих) − нейтраль, ×2:
# обе подпитывают сферу → +4, одна → 0, ни одна → −4. Работает и без эфемерид.
_ELEMENT_AFFINITY = {
    "огонь":   {"love": 2, "harmony": 0, "career": 1, "friendship": 0, "growth": 1},
    "земля":   {"love": 0, "harmony": 2, "career": 1, "friendship": 0, "growth": 1},
    "воздух":  {"love": 0, "harmony": 0, "career": 1, "friendship": 2, "growth": 1},
    "вода":    {"love": 2, "harmony": 2, "career": 0, "friendship": 1, "growth": 1},
}


def _sphere_values(base: int, lunar: int, venus: int, cross: int,
                   e1: str, e2: str) -> dict[str, int]:
    """Пять сфер из тех же данных пары, каждая со своим акцентом (0..100)."""
    def clamp(v: float) -> int:
        return max(0, min(100, round(v)))
    a1, a2 = _ELEMENT_AFFINITY[e1], _ELEMENT_AFFINITY[e2]
    offsets = {s: (a1[s] + a2[s] - 2) * 2 for s in _SPHERE_ORDER}
    return {
        "love":       clamp(base + offsets["love"] + 2 * venus + lunar + cross),
        "harmony":    clamp(base + offsets["harmony"] + 2 * lunar + venus),
        "career":     clamp(base + offsets["career"] + cross),
        "friendship": clamp(base + offsets["friendship"] + lunar + cross),
        "growth":     clamp(base + offsets["growth"] + lunar + venus + cross),
    }


def _sphere_notes(e1: str, e2: str) -> dict[str, str]:
    """Живые подписи сфер — от стихий, а не от волшебной таблицы.

    Порядок пары каноничный (пары симметричны): подпись не должна меняться
    от того, кто спросил.
    """
    if e1 == e2:
        flavor = f"вас объединяет общая стихия {e1} — на одной волне"
    else:
        x, y = sorted((e1, e2))
        if frozenset([e1, e2]) in (frozenset(["огонь", "воздух"]),
                                   frozenset(["земля", "вода"])):
            flavor = f"{x} и {y} подпитывают друг друга"
        else:
            flavor = f"{x} и {y} учатся друг у друга"
    return {
        "love": f"химия и притяжение: {flavor}",
        "harmony": "быт и уют — как делите дом, время и заботу о мелочах",
        "career": "дело и деньги — вы друг другу союзники или соперники?",
        "friendship": "доверие и поддержка — насколько легко молчать вдвоём",
        "growth": "общий вектор — тянет ли расти в одну сторону",
    }


def _compat(user_birth: str, partner_birth: str, relation: str = "love",
            aspects: list[dict] | None = None) -> dict:
    """Совместимость пары по реальным точкам карты — по сферам жизни.

    Формула одна на весь продукт: бот, Mini App и ответ Оракула обязаны называть
    одно и то же число, иначе клиентка видит противоречие и теряет доверие.
    Базой служат стихии Солнц, поверх — Луна (душа), Венера (любовь) и крест
    «Солнце-Луна» — это сильнейшие синастрические нити по датам без времени.
    Дальше балл разворачивается в пять сфер жизни (каждая считается из этих же
    данных), а итоговый total — их взвешенное среднее по типу связи. Все значения
    детерминированы и симметричны: не зависят от того, кто спросил. `score` —
    алиас `total`, чтобы старый код (бот, Mini App, кэш разборов) не падал.

    `aspects` — синастрические аспекты пары (мажорные, из полных карт). Когда
    карты обеих есть, их вклад (trine +6, sextile +4, conjunction +3, square −4,
    opposition −3) двигает итог и попадает в breakdown отдельной строкой «Синастрия
    карт». Без карт (аспектов нет) балл остаётся по датам — лёгкий путь без
    kerykeion работает так же, как раньше.
    """
    aspects = aspects or []
    relation = relation if relation in _RELATION_WEIGHTS else "love"
    d1 = datetime.strptime(user_birth, "%Y-%m-%d").date()
    d2 = datetime.strptime(partner_birth, "%Y-%m-%d").date()
    s1, _, e1 = astro.sun_sign_precise(d1)
    s2, _, e2 = astro.sun_sign_precise(d2)
    m1, v1 = astro.moon_venus_signs(d1)
    m2, v2 = astro.moon_venus_signs(d2)

    base = ELEMENT_SCORE.get(frozenset([e1, e2]), 60)
    if e1 == e2:
        broken = f"обе {e1}"
    elif frozenset([e1, e2]) in (frozenset(["огонь", "воздух"]),
                                 frozenset(["земля", "вода"])):
        broken = f"{e1} и {e2} — питают друг друга"
    else:
        broken = f"{e1} и {e2} — рост через трение"
    breakdown = [{"title": "Стихии Солнца", "value": base, "note": broken}]

    lunar = _element_bonus(m1[1] if m1 else None, m2[1] if m2 else None)
    if lunar:
        breakdown.append({"title": "Луна (душа)", "value": lunar,
                          "note": ("как вы чувствуете друг друга без слов — "
                                   "стихия ваших Лун: согревает или остужает")})

    venus = _element_bonus(v1[1] if v1 else None, v2[1] if v2 else None)
    if venus:
        breakdown.append({"title": "Венера (любовь)", "value": venus,
                          "note": ("как вы притягиваетесь и что цените друг в "
                                   "друге — стихия ваших Венер")})

    cross = (_element_bonus(m2[1] if m2 else None, e1)
             + _element_bonus(m1[1] if m1 else None, e2))
    if cross:
        breakdown.append({"title": "Крест Солнце-Луна", "value": cross,
                          "note": ("его Солнце встречает её Луну и наоборот — "
                                   "самая живая нить синастрии: кто кого "
                                   "согревает и кто чью воду тушит")})

    values = _sphere_values(base, lunar, venus, cross, e1, e2)
    notes = _sphere_notes(e1, e2)
    weights = _RELATION_WEIGHTS[relation]
    total = round(sum(values[s] * weights[s] for s in _SPHERE_ORDER))
    if aspects:
        bonus = synastry_bonus(aspects)
        breakdown.append({"title": "Синастрия карт", "value": bonus,
                          "note": (f"{astro.synastry_aspects_text(aspects)}. "
                                   f"Вклад аспектов в балл: {bonus:+d}")})
        total += bonus
    total = max(35, min(98, total))
    spheres = [{"slug": slug, "title": _SPHERE_DEFS[slug],
                "value": values[slug], "note": notes[slug]}
               for slug in _SPHERE_ORDER]
    return {"you": {"sign": s1, "element": e1},
            "partner": {"sign": s2, "element": e2},
            "total": total, "score": total, "relation": relation,
            "verdict": _verdict(total, e1, e2),
            "breakdown": breakdown, "spheres": spheres}


def compatibility_score(user_birth: str, partner_birth: str,
                        relation: str = "love",
                        aspects: list[dict] | None = None) -> dict:
    """Публичный доменный API расчёта совместимости."""
    return _compat(user_birth, partner_birth, relation=relation, aspects=aspects)


_ELEMENT_VERB = {
    ("огонь", "огонь"): "союз-пламя: вы зажигаете друг друга",
    ("земля", "земля"): "союз-основа: вы строите надёжное",
    ("воздух", "воздух"): "союз-ветер: вы свободно дышите вместе",
    ("вода", "вода"): "союз-глубина: вы чувствуете друг друга без слов",
}


def _verdict(score: int, e1: str, e2: str) -> str:
    """Вердикт по стихии пары — «пламя» уходит только паре из огня."""
    by_style = _ELEMENT_VERB.get((e1, e2)) or _ELEMENT_VERB.get((e2, e1))
    if score >= 80:
        return by_style or "союз-гармония: вы дополняете друг друга"
    if score >= 60:
        return "союз-рост: разность стихий учит вас обоих"
    return "союз-урок: трение сильное, но именно оно шлифует"


async def pair_aspects(db, user: dict, partner_birth: str) -> list[dict] | None:
    """Мажорные аспекты пары из двух полных карт; None, если карт нет.

    Карта партнёра — из сохранённых людей по дате рождения (её полную строим,
    когда клиентка указывала город и время). Нет карт — возвращаем None, и балл
    остаётся строго по датам: лёгкий путь без kerykeion работает как раньше.
    Модель аспекты не выдумывает — их считает `astro.synastry_aspects`.
    """
    try:
        chart = json.loads(user["chart_json"] or "{}")
        if chart.get("mode") != "full" or not chart.get("planets"):
            return None
        partner = await readings_repo.find_partner_by_date(
            db, user["tg_id"], partner_birth)
        if not partner:
            return None
        pchart = json.loads(partner["chart_json"] or "{}") \
            if partner["chart_json"] else {}
        if pchart.get("mode") != "full" or not pchart.get("planets"):
            return None
        return astro.synastry_aspects(chart["planets"], pchart["planets"])
    except (json.JSONDecodeError, TypeError, ValueError, KeyError, AttributeError):
        return None


# Legacy alias: bot and older agent tools migrate incrementally.
_pair_aspects = pair_aspects


# ---------------------------------------------------------------- placements and palmistry

_PLACEMENT_CODES = tuple(placements.PLACEMENT_META) + ("life_path", "chinese_zodiac")


def _placement_inputs(user) -> dict:
    return {
        "birth_date": user["birth_date"],
        "birth_time": user["birth_time"],
        "city": user["birth_city"],
        "lat": user["birth_lat"],
        "lon": user["birth_lon"],
        "tz": user["tz"],
        "time_known": bool(user["birth_time_known"]),
    }


async def _run_get_placement(db, user, args) -> str:
    code = str(args.get("placement", "") or "").strip()
    if not user["birth_date"]:
        return "нет даты рождения — сначала собери натальную карту"
    if code not in _PLACEMENT_CODES:
        available = ", ".join(_PLACEMENT_CODES)
        return f"неизвестный placement: выбери один из {available}"
    if code == "life_path":
        result = placements.life_path(user["birth_date"])
    elif code == "chinese_zodiac":
        result = placements.chinese_zodiac(user["birth_date"])
    else:
        result = placements.calculate_placement(code, **_placement_inputs(user))
    return f"[Детерминированный evidence placement — не выдумывай факты]\n{placements.as_tool_json(result)}"


async def _run_get_all_placements(db, user, args) -> str:
    if not user["birth_date"]:
        return "нет даты рождения — сначала собери натальную карту"
    result = placements.all_calculators(**_placement_inputs(user))
    return ("[Детерминированный evidence всех placement-калькуляторов — "
            "трактуй только эти значения]\n" + placements.as_tool_json(result))


async def _run_get_life_path(db, user, args) -> str:
    if not user["birth_date"]:
        return "нет даты рождения"
    return placements.as_tool_json(placements.life_path(user["birth_date"]))


async def _run_get_chinese_zodiac(db, user, args) -> str:
    if not user["birth_date"]:
        return "нет даты рождения"
    return placements.as_tool_json(placements.chinese_zodiac(user["birth_date"]))


PALM_TOPIC_LABELS = {
    "heart_line": "линия сердца", "head_line": "линия головы",
    "life_line": "линия жизни", "fate_line": "линия судьбы",
    "sun_line": "линия Солнца", "mercury_line": "линия Меркурия (здоровья)",
    "relationship_line": "линии брака и отношений",
    "children_lines": "линии детей",
    "travel_lines": "линии путешествий",
    "girdle_of_venus": "кольцо Венеры", "bracelets": "браслеты запястья",
    "mounts": "холмы", "fingers": "пальцы",
}

async def _run_palm_scanner(db, user, args) -> str:
    reading = await palm.latest(db, user)
    if not reading:
        return ("чтений ладони пока нет — попроси загрузить чёткое фото одной ладони "
                "(ровный свет, камера сверху, ладонь целиком)")
    quality = reading.get("image_quality") or {}
    score = 0
    try:
        score = float(quality.get("score") or 0)
    except (TypeError, ValueError):
        pass
    usable = reading.get("status") == "complete" and score >= 0.6
    if not usable:
        return ("кадр недостаточно качественный для разбора — предложи переснять ладонь целиком "
                "при ровном свете, без бликов и фильтров")
    zones = []
    for item in reading.get("observations") or []:
        topic = str(item.get("topic") or "unknown")
        zones.append({
            "topic": topic,
            "label": PALM_TOPIC_LABELS.get(topic, topic),
            "visibility": item.get("visibility", "unclear"),
            "confidence": item.get("confidence", 0),
            "summary": item.get("summary", ""),
        })
    geometry = reading.get("hand_geometry") or {}
    geometry_summary = {
        "version": geometry.get("version"),
        "status": geometry.get("status", "unavailable"),
        "hand_count": geometry.get("hand_count", 0),
        "model": geometry.get("model"),
        "hands": [{
            "handedness": hand.get("handedness", "unknown"),
            "handedness_score": hand.get("handedness_score"),
            "normalized_bbox": hand.get("normalized_bbox"),
            "landmark_count": hand.get("landmark_count", 0),
        } for hand in (geometry.get("hands") or [])],
        "line_segmentation": "not_attempted",
    }
    payload = {
        "reading_id": reading.get("id"),
        "hand_side": reading.get("hand_side", "unknown"),
        "hand_shape_element": reading.get("hand_shape_element", "unknown"),
        "image_quality": {"score": round(score, 2), "issues": quality.get("issues") or [],
                           "precheck_score": quality.get("precheck_score", score),
                           "precheck_issues": quality.get("precheck_issues") or []},
        "visual_precheck": reading.get("visual_precheck") or {},
        "hand_geometry": geometry_summary,
        "zones": zones,
        "lines": reading.get("lines") or {},
        "mounts": reading.get("mounts") or {},
        "fingers": reading.get("fingers") or {},
        "interpretive_prompts": reading.get("interpretive_prompts") or [],
        "limitations": reading.get("limitations") or [],
        "rule": ("Только символическая хиромантия по видимому: не добавляй невидимые признаки, "
                 "без медицинских выводов, предсказаний и сроков."),
    }
    return "[Полное сканирование ладони — evidence vision-наблюдений]\n" + json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"))


PALM_PHOTO_GUIDE = (
    "[Какие фото ладони нужны — по правилам хиромантии]\n"
    "1. РАСКРЫТАЯ ладонь целиком, ровный свет, камера сверху: линии жизни/головы/"
    "сердца/судьбы/Солнца, холмы, пальцы и тип руки по стихии.\n"
    "2. СОГНУТАЯ ладонь (сжать четыре пальца, ребро ладони к камере): единственный "
    "ракурс, где видны линии брака/отношений, линии детей и линии путешествий. "
    "На раскрытой ладони их НЕ видно.\n"
    "3. Общие требования к любому кадру: чёткость без размытия, ровный свет без "
    "бликов и теней от пальцев, без фильтров; тёмные линии на светлой руке читаются "
    "лучше всего.\n"
    "4. Проверь photo_assessment из palm_scanner: если view_type=open_palm и зоны "
    "брака/детей помечены not_visible — попроси второе фото с согнутой ладонью."
)


async def _run_palm_photo_guide(db, user, args) -> str:
    reading = await palm.latest(db, user)
    advice = []
    if reading:
        pa = reading.get("photo_assessment") or {}
        advice = [str(a) for a in (pa.get("advice") or [])]
        missing = [str(m) for m in (pa.get("missing_views") or [])]
        if missing:
            advice.append("не хватает ракурсов: " + ", ".join(missing))
        vt = str(pa.get("view_type") or "")
        if vt == "open_palm":
            advice.append("раскрытая ладонь есть — для линий брака/детей нужен кадр "
                          "с согнутой ладонью (ребро к камере)")
    lines = [PALM_PHOTO_GUIDE]
    if advice:
        lines.append("\nПерсонально для последнего снимка:\n- " + "\n- ".join(advice[:8]))
    return "\n".join(lines)


async def _run_palm_history(db, user, args) -> str:
    try:
        requested = int(args.get("limit", 10) or 10)
    except (TypeError, ValueError):
        requested = 10
    readings = await palm_repo.list_readings(
        db, user["tg_id"], limit=max(1, min(requested, 20)))
    if not readings:
        return ("чтений ладони ещё нет — попроси фото раскрытой ладони целиком "
                "(ровный свет, камера сверху)")
    return ("Сохранённые чтения ладони (новые первыми):\n" + "\n".join(
        f"- id={r['id']}: {r['created_at'][:16]}, рука {r['hand_side'] or 'неизвестна'}, "
        f"статус {r['status']}" for r in readings))


# ---------------------------------------------------------------- skills

async def _run_draw_tarot(db, user, args) -> str:
    try:
        requested = int(args.get("n", 3) or 3)
    except (TypeError, ValueError):
        return "число карт должно быть целым от 1 до 12"
    n = max(1, min(requested, 12))
    requested_deck = args.get("deck_id")
    try:
        selected = tarot.deck_metadata(requested_deck or (
            user["tarot_deck_id"] if "tarot_deck_id" in user.keys() else None))
    except ValueError:
        return "неизвестная колода — выбери её из каталога"
    selected_id = selected["deck_id"]
    spread_code = str(args.get("spread", "") or "").strip()
    available = tarot.spreads_for(selected_id)
    if spread_code and spread_code not in available:
        return "неизвестная схема расклада для выбранной колоды — выбери доступную схему из каталога"
    item = tarot.spread_for(spread_code, selected_id) if spread_code else None
    positions = item["positions"] if item and spread_code in available else None
    if positions:
        n = len(positions)
    cards = tarot.draw(n, deck_id=selected_id)
    title = item["title"] if item else "свободный"
    ledger = tarot.reading_ledger(cards, spread_code or tarot.DEFAULT_SPREAD,
                                  positions=positions, deck_id=selected_id)
    return (f"{await guide(db, 'tarot')}\n\nРасклад: {title}\n"
            f"Карты:\n{tarot.cards_text(cards, positions)}\n"
            "\nEvidence ledger:\n" + json.dumps(ledger, ensure_ascii=False, separators=(",", ":")))


async def _run_get_chart(db, user, args) -> str:
    try:
        chart = json.loads(user["chart_json"] or "{}")
    except (TypeError, ValueError):
        chart = {}
    if not chart:
        return "карта ещё не построена — попроси клиентку пройти /start"
    known = "точное" if user["birth_time_known"] else "НЕТОЧНОЕ (дома не использовать)"
    lines = [await guide(db, "natal"), "", f"Время рождения: {known}",
             astro.chart_brief(chart, time_known=bool(user["birth_time_known"]))]
    houses = chart.get("houses") or []
    if houses and user["birth_time_known"]:
        lines.append("Куспиды домов: " + "; ".join(
            f"{h['n']}-й в {h['sign']}" for h in houses))
    return "\n".join(lines)


async def _run_get_transits(db, user, args) -> str:
    sky = astro.today_sky()
    try:
        chart = json.loads(user["chart_json"] or "{}")
    except (TypeError, ValueError):
        chart = {}
    sun = (chart.get("sun") or {}).get("sign", "?")
    # Реальное небо из эфемерид, а не только «лунная фаза»: знаки Луны и Венеры
    # меняются медленно и дают контекст для трактовки чувств и ценностей.
    extras = []
    moon, venus = astro.moon_venus_signs(date.today())
    if moon:
        extras.append(f"Луна в {moon[0]} ({moon[1]}) — как сегодня отзывается душа")
    if venus:
        extras.append(f"Венера в {venus[0]} ({venus[1]}) — что сейчас притягивает в любви")
    sky_line = (f"Луна: {sky['moon']['emoji']} {sky['moon']['name']} "
                f"({sky['moon']['advice']}), лунный день ~{sky['moon']['day']}")
    if extras:
        sky_line += "; " + "; ".join(extras)
    return (f"{await guide(db, 'transit')}\n\nСегодня: сезон Солнца в "
            f"{sky['sun_season']['sign']}, {sky_line}. Её Солнце: {sun}.")


async def _run_moon_week(db, user, args) -> str:
    """Лунный календарь на неделю — для планирования, а не «на сегодня»."""
    today = date.today()
    lines = []
    for i in range(7):
        d = today + timedelta(days=i)
        phase = astro.moon_phase(d)
        moon_sig = ""
        moon = astro.moon_venus_signs(d)[0]
        if moon:
            moon_sig = f", Луна в {moon[0]}"
        lines.append(f"{d.strftime('%d.%m')}: {phase['emoji']} {phase['name']} "
                     f"({phase['day']}-й лунный день){moon_sig} — {phase['advice']}")
    return f"{await guide(db, 'transit')}\n\nЛунная неделя:\n" + "\n".join(lines)


# Что фаза Луны даёт деловым решениям. Астрологический электив в его самой
# практичной части: начинать — на растущей, завершать и увольняться — на убывающей.
_CAREER_WINDOWS = {
    "Новолуние": ("старт", "писать планы и намерения, собирать идеи — но не подписывать"),
    "Растущий серп": ("старт", "первые шаги вслух: отклики, знакомства, пробные разговоры"),
    "Первая четверть": ("решение", "решать и снимать сомнения — половина пути уже за тобой"),
    "Растущая Луна": ("действие", "подписывать, запускать, просить повышение — время силы"),
    "Полнолуние": ("осторожно", "эмоции громче фактов — не подписывать и не ссориться"),
    "Убывающая Луна": ("завершение", "закрывать долги и хвосты, благодарить, отпускать"),
    "Последняя четверть": ("завершение", "увольняться и расставаться с лишним — чисто, без драм"),
    "Старый серп": ("пауза", "выдыхать и копить силы — новое начинать рано"),
}


async def _run_career_windows(db, user, args) -> str:
    """Деловые окна на две недели: когда действовать, когда молчать."""
    try:
        requested = int(args.get("days", 14) or 14)
    except (TypeError, ValueError):
        return "горизонт должен быть целым числом от 7 до 30 дней"
    days = max(7, min(requested, 30))
    today = date.today()
    lines = []
    for i in range(days):
        d = today + timedelta(days=i)
        phase = astro.moon_phase(d)
        kind, advice = _CAREER_WINDOWS.get(phase["name"], ("нейтрально", "обычный день"))
        weekday = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"][d.weekday()]
        lines.append(f"{d.strftime('%d.%m')} ({weekday}) {phase['emoji']} "
                     f"{phase['name']} — [{kind}] {advice}")
    return (f"{await guide(db, 'career')}\n\nДеловые окна на {days} дней:\n"
            + "\n".join(lines))


async def _run_get_matrix(db, user, args) -> str:
    if not user["birth_date"]:
        return "нет данных рождения"
    m = compute_matrix(user["birth_date"])
    return f"{await guide(db, 'matrix')}\n\n{matrix_brief(m)}"


async def _run_compatibility(db, user, args) -> str:
    partner = str(args.get("partner_birth_date", "") or "").strip()
    relation = str(args.get("relation", "love") or "love").strip().lower()
    if relation not in _RELATION_LABEL:
        return "тип связи должен быть love, friend, work или family"
    try:
        datetime.strptime(partner, "%Y-%m-%d")
    except (TypeError, ValueError):
        return "нужна дата партнёра в формате YYYY-MM-DD — уточни её у клиентки"
    if not user["birth_date"]:
        return "нет даты рождения клиентки"
    aspects = await _pair_aspects(db, user, partner)
    c = _compat(user["birth_date"], partner, relation=relation, aspects=aspects)
    label = _RELATION_LABEL.get(relation, "любовная пара")
    spheres = "\n".join(
        f"- {s['title']}: {s['value']}/100 — {s['note']}" for s in c["spheres"])
    synast = ""
    if aspects:
        synast = (f"\n\nСинастрия по полным картам: "
                  f"{astro.synastry_aspects_text(aspects)} "
                  f"(вклад в балл {synastry_bonus(aspects):+d}). "
                  f"Используй эти аспекты в разборе.")
    return (f"{await guide(db, 'compat')}\n\nОна: {c['you']['sign']} "
            f"({c['you']['element']}), {label}: {c['partner']['sign']} "
            f"({c['partner']['element']}). Балл совместимости: {c['score']}/100 — "
            f"{c['verdict']}.{synast}\n\nСферы:\n{spheres}\n\nРазбери совместимость "
            f"по сферам и по типу связи ({label}): где сильные стороны и где "
            f"зоны работы. Тепло и конкретно.")


async def _run_list_partners(db, user, args) -> str:
    partners = await readings_repo.list_partners(db, user["tg_id"])
    if not partners:
        return "в её окружении пока никто не сохранён"
    return "Люди, которых она сохранила:\n" + "\n".join(
        f"- {p['name'] or 'без имени'} ({p['relation']}), рождение {p['birth_date']}"
        for p in partners)


async def _run_save_memory(db, user, args) -> str:
    # Privacy is enforced here as well as in the HTTP/service layer. Tool calls
    # are model-generated and must never be able to override the user's setting.
    if not bool(user["memory_enabled"]):
        return "память выключена — факт не сохранён"
    fact = str(args.get("fact", "") or "").strip()[:1000]
    if not fact:
        return "нечего сохранять"
    kind = str(args.get("kind", "fact") or "fact").strip().lower()
    if kind not in {"person", "event", "emotion", "goal", "fact"}:
        kind = "fact"
    saved = await memory.remember(db, user["tg_id"], fact, kind=kind)
    return "сохранено" if saved else "уже знаю это — усилила важность"


async def _run_recall_memory(db, user, args) -> str:
    if not bool(user["memory_enabled"]):
        return "память выключена — сохранённые факты не используются"
    query = str(args.get("query", "") or "").strip()[:200]
    if not query:
        return "укажи короткую тему для поиска в памяти"
    mems = await memory.recall(db, user["tg_id"], query, limit=12)
    return "\n".join(f"- {m}" for m in mems) or "память пуста"


async def _run_recall_diary(db, user, args) -> str:
    if not bool(user["memory_enabled"]):
        return "память выключена — дневник не передаётся проводнику"
    entries = await dialog_repo.get_diary(db, user["tg_id"], limit=10)
    if not entries:
        return "дневник пока пуст"
    streak = await dialog_repo.diary_streak(db, user["tg_id"])
    lines = [f"{e['created_at'][:10]}: {e['text'][:200]}" for e in entries]
    return (f"{await guide(db, 'diary')}\n\nСтрик: {streak} дн.\n"
            "Последние записи:\n" + "\n".join(lines))


async def _run_suggest_practice(db, user, args) -> str:
    """Каталог практик под её запрос + что у неё уже идёт.

    Модель не придумывает ритуалы: она выбирает из каталога, потому что шаги,
    сроки и предупреждения (например, «это к психологу») выверены в контенте.
    """
    from ..services import practices as practices_svc

    category = str(args.get("category", "") or "").strip() or None
    items = await practices_svc.list_for_user(db, user, category=category)
    if not items:
        return "подходящих практик в каталоге нет"
    lines = [await guide(db, "practice"), ""]
    running = [p for p in items if p["started"] and not p["finished"]]
    if running:
        lines.append("Уже идут у неё:")
        lines += [f"- {p['title']}: день {p['day_index']} из {p['days']}, "
                  f"стрик {p['streak']}" for p in running]
        lines.append("")
    lines.append("Каталог (код — название — для чего — сколько дней):")
    for p in items[:14]:
        lines.append(f"- {p['code']} — {p['title']} — {p['goal']} — "
                     f"{p['days']} дн." + (" [уже идёт]" if p["started"] else ""))
    lines.append("\nПредложи ОДНУ практику, объясни почему именно её, назови срок "
                 "и скажи, что открыть её можно в разделе «Дневник» → «Практики».")
    return "\n".join(lines)


def _user_field(user, key: str, default=None):
    try:
        return user[key]
    except (KeyError, IndexError, TypeError):
        return default


async def _run_get_vedic_chart(db, user, args) -> str:
    if not _user_field(user, "birth_date"):
        return "нет даты рождения — сначала собери натальную карту"
    try:
        result = vedic.compute_vedic_chart(
            user["birth_date"], _user_field(user, "birth_time"), _user_field(user, "birth_city"),
            _user_field(user, "birth_lat"), _user_field(user, "birth_lon"), _user_field(user, "tz"),
            time_known=bool(_user_field(user, "birth_time_known")),
        )
    except (TypeError, ValueError) as exc:
        return f"Vedic chart unavailable: {exc}"
    return "[Vedic evidence — Lahiri sidereal, do not invent fields]\n" + json.dumps(result, ensure_ascii=False, separators=(",", ":"))


async def _run_get_nakshatra(db, user, args) -> str:
    try:
        longitude = float(args.get("longitude"))
        result = vedic.get_nakshatra(longitude)
    except (TypeError, ValueError) as exc:
        return f"longitude must be between 0 and 360 degrees: {exc}"
    return "[Vedic evidence — nakshatra/pada]\n" + json.dumps(result, ensure_ascii=False, separators=(",", ":"))


async def _run_get_vimshottari_dasha(db, user, args) -> str:
    if not _user_field(user, "birth_date") or not _user_field(user, "birth_time"):
        return "для точной Vimshottari Dasha нужны дата и подтверждённое время рождения"
    try:
        result = vedic.get_vimshottari_dasha(
            user["birth_date"], user["birth_time"], _user_field(user, "tz"),
            as_of=args.get("as_of"),
        )
    except (TypeError, ValueError) as exc:
        return f"Vimshottari unavailable: {exc}"
    return "[Vedic evidence — Vimshottari timeline]\n" + json.dumps(result, ensure_ascii=False, separators=(",", ":"))


async def _run_get_panchang(db, user, args) -> str:
    calendar_date = str(args.get("date") or date.today().isoformat())
    try:
        result = vedic.get_panchang(calendar_date, _user_field(user, "birth_lat"), _user_field(user, "birth_lon"), _user_field(user, "tz"))
    except (TypeError, ValueError) as exc:
        return f"Panchang unavailable: {exc}"
    return "[Vedic evidence — Panchang]\n" + json.dumps(result, ensure_ascii=False, separators=(",", ":"))


async def _run_get_rahu_kaal(db, user, args) -> str:
    calendar_date = str(args.get("date") or date.today().isoformat())
    try:
        result = vedic.get_rahu_kaal(calendar_date, _user_field(user, "birth_lat"), _user_field(user, "birth_lon"), _user_field(user, "tz"))
    except (TypeError, ValueError) as exc:
        return f"Rahu Kaal unavailable: {exc}"
    return "[Vedic evidence — Rahu Kaal, traditional planning convention]\n" + json.dumps(result, ensure_ascii=False, separators=(",", ":"))


async def _run_get_varga_chart(db, user, args) -> str:
    try:
        chart = vedic.compute_vedic_chart(
            user["birth_date"], _user_field(user, "birth_time"), _user_field(user, "birth_city"),
            _user_field(user, "birth_lat"), _user_field(user, "birth_lon"), _user_field(user, "tz"),
            time_known=bool(_user_field(user, "birth_time_known")),
        )
        result = vedic.get_varga_chart(chart["result"], str(args.get("varga") or "D1"))
    except (KeyError, TypeError, ValueError) as exc:
        return f"Varga unavailable: {exc}"
    return "[Vedic evidence — divisional chart]\n" + json.dumps(result, ensure_ascii=False, separators=(",", ":"))


async def _run_get_guna_milan(db, user, args) -> str:
    partner_date = str(args.get("partner_birth_date") or "").strip()
    if not _user_field(user, "birth_date") or not partner_date:
        return "для Guna Milan нужны даты рождения обоих людей"
    try:
        own = vedic.compute_vedic_chart(
            user["birth_date"], _user_field(user, "birth_time"), _user_field(user, "birth_city"),
            _user_field(user, "birth_lat"), _user_field(user, "birth_lon"), _user_field(user, "tz"),
            time_known=bool(_user_field(user, "birth_time_known")),
        )
        partner_time = str(args.get("partner_birth_time") or "12:00")
        partner = vedic.compute_vedic_chart(partner_date, partner_time, None,
                                            _user_field(user, "birth_lat"), _user_field(user, "birth_lon"), _user_field(user, "tz"),
                                            time_known=bool(args.get("partner_time_known", False)))
        result = vedic.get_guna_milan(own["result"], partner["result"])
    except (KeyError, TypeError, ValueError) as exc:
        return f"Guna Milan unavailable: {exc}"
    return "[Vedic evidence — Ashtakoot/Guna Milan]\n" + json.dumps(result, ensure_ascii=False, separators=(",", ":"))


async def _run_get_vedic_transits(db, user, args) -> str:
    try:
        result = vedic.get_vedic_transits(args.get("as_of"))
    except (TypeError, ValueError) as exc:
        return f"Vedic transits unavailable: {exc}"
    return "[Vedic evidence — sidereal transits]\n" + json.dumps(result, ensure_ascii=False, separators=(",", ":"))


async def _run_get_graha_strengths(db, user, args) -> str:
    if not _user_field(user, "birth_date"):
        return "нет даты рождения — сначала собери натальную карту"
    try:
        chart = vedic.compute_vedic_chart(
            user["birth_date"], _user_field(user, "birth_time"), _user_field(user, "birth_city"),
            _user_field(user, "birth_lat"), _user_field(user, "birth_lon"), _user_field(user, "tz"),
            time_known=bool(_user_field(user, "birth_time_known")),
        )
        result = vedic.get_graha_strengths(chart["result"])
    except (KeyError, TypeError, ValueError) as exc:
        return f"Graha strengths unavailable: {exc}"
    return "[Vedic evidence — dignity-lite strengths, not full Shadbala]\n" + json.dumps(result, ensure_ascii=False, separators=(",", ":"))


async def _run_get_muhurta(db, user, args) -> str:
    try:
        result = vedic.get_muhurta(
            str(args.get("date_a") or ""), str(args.get("date_b") or ""),
            _user_field(user, "birth_lat"), _user_field(user, "birth_lon"), _user_field(user, "tz"),
            str(args.get("criteria") or ""),
        )
    except (TypeError, ValueError) as exc:
        return f"Muhurta unavailable: {exc}"
    return "[Vedic evidence — criteria comparison, no guarantee]\n" + json.dumps(result, ensure_ascii=False, separators=(",", ":"))


SKILLS: dict[str, dict] = {
    "get_vedic_chart": {
        "run": _run_get_vedic_chart,
        "schema": {"name": "get_vedic_chart", "description": (
            "Vedic/Jyotish Kundli по sidereal Lahiri: graha, Rahu/Ketu, nakshatra "
            "и whole-sign houses только при подтверждённом времени."),
            "input_schema": {"type": "object", "properties": {}}},
    },
    "get_nakshatra": {
        "run": _run_get_nakshatra,
        "schema": {"name": "get_nakshatra", "description": (
            "Детерминированно определить 27 nakshatra, pada и lord по долготе 0-360°."),
            "input_schema": {"type": "object", "properties": {
                "longitude": {"type": "number", "description": "Sidereal longitude 0-360"}},
                "required": ["longitude"]}},
    },
    "get_vimshottari_dasha": {
        "run": _run_get_vimshottari_dasha,
        "schema": {"name": "get_vimshottari_dasha", "description": (
            "Vimshottari Mahadasha timeline from Moon nakshatra; requires precise birth time."),
            "input_schema": {"type": "object", "properties": {
                "as_of": {"type": "string", "description": "Optional YYYY-MM-DD snapshot"}}}},
    },
    "get_panchang": {
        "run": _run_get_panchang,
        "schema": {"name": "get_panchang", "description": (
            "Local Vedic Panchang: vara, tithi, nakshatra, yoga, karana, sunrise/sunset."),
            "input_schema": {"type": "object", "properties": {
                "date": {"type": "string", "description": "Local YYYY-MM-DD"}}}},
    },
    "get_rahu_kaal": {
        "run": _run_get_rahu_kaal,
        "schema": {"name": "get_rahu_kaal", "description": (
            "Local Rahu Kaal interval from sunrise/sunset; traditional planning convention only."),
            "input_schema": {"type": "object", "properties": {
                "date": {"type": "string", "description": "Local YYYY-MM-DD"}}}},
    },
    "get_varga_chart": {
        "run": _run_get_varga_chart,
        "schema": {"name": "get_varga_chart", "description": (
            "Vedic divisional chart using documented D1, D9 Navamsa or D10 Dasamsa rule."),
            "input_schema": {"type": "object", "properties": {
                "varga": {"type": "string", "enum": ["D1", "D9", "D10"]}},
                "required": ["varga"]}},
    },
    "get_guna_milan": {
        "run": _run_get_guna_milan,
        "schema": {"name": "get_guna_milan", "description": (
            "Ashtakoot/Guna Milan breakdown, maximum 36; score is not a relationship verdict."),
            "input_schema": {"type": "object", "properties": {
                "partner_birth_date": {"type": "string", "description": "Partner YYYY-MM-DD"},
                "partner_birth_time": {"type": "string", "description": "Optional HH:MM"},
                "partner_time_known": {"type": "boolean"}},
                "required": ["partner_birth_date"]}},
    },
    "get_vedic_transits": {
        "run": _run_get_vedic_transits,
        "schema": {"name": "get_vedic_transits", "description": (
            "Sidereal Lahiri transit positions for an as-of date with explicit tradition marker."),
            "input_schema": {"type": "object", "properties": {
                "as_of": {"type": "string", "description": "Optional YYYY-MM-DD"}}}},
    },
    "get_graha_strengths": {
        "run": _run_get_graha_strengths,
        "schema": {"name": "get_graha_strengths", "description": (
            "Bounded sign-dignity evidence with formula metadata; not full Shadbala."),
            "input_schema": {"type": "object", "properties": {}}},
    },
    "get_muhurta": {
        "run": _run_get_muhurta,
        "schema": {"name": "get_muhurta", "description": (
            "Compare two local dates using explicit user criteria; never a guaranteed auspiciousness claim."),
            "input_schema": {"type": "object", "properties": {
                "date_a": {"type": "string", "description": "Candidate A YYYY-MM-DD"},
                "date_b": {"type": "string", "description": "Candidate B YYYY-MM-DD"},
                "criteria": {"type": "string", "description": "User's practical criterion"}},
                "required": ["date_a", "date_b"]}},
    },
    "draw_tarot": {
        "run": _run_draw_tarot,
        "schema": {
            "name": "draw_tarot",
            "description": ("Вытянуть карты из выбранной tradition (RWS, Petit Lenormand "
                            "или Tarot de Marseille) с evidence ledger. "
                            "Зови, когда нужен расклад или клиентка просит «что говорят карты»."),
            "input_schema": {"type": "object", "properties": {
                "n": {"type": "integer", "description": "Число карт 1-12"},
                "spread": {"type": "string",
                           "description": "Код схемы выбранной tradition: one, three, love, choice, "
                                          "money, career, work, celtic, year или line5"},
                "deck_id": {"type": "string", "description": "ID колоды из tarot deck catalog"},
            }, "required": ["n"]},
        },
    },
    "get_chart": {
        "run": _run_get_chart,
        "schema": {
            "name": "get_chart",
            "description": ("Натальная карта клиентки (планеты/знаки/дома/аспекты). Зови "
                            "для вопросов о характере, предназначении, «почему я такая»."),
            "input_schema": {"type": "object", "properties": {}},
        },
    },
    "get_placement": {
        "run": _run_get_placement,
        "schema": {
            "name": "get_placement",
            "description": ("Детерминированный placement-калькулятор по сохранённым "
                            "данным рождения. Вызывай перед любым утверждением о "
                            "Луне, Венере, Марсе, Меркурии, Юпитере, Сатурне, "
                            "Уране, Нептуне, Плутоне, Хироне, Джуно, астероидах, "
                            "узлах или Асценденте."),
            "input_schema": {"type": "object", "properties": {
                "placement": {"type": "string", "enum": [
                    "moon_sign", "venus_sign", "rising_sign", "asteroid_sign",
                    "chiron_sign", "juno_sign", "jupiter_sign", "mars_sign",
                    "mercury_sign", "neptune_sign", "north_node_sign", "rahu_sign",
                    "pluto_sign", "saturn_sign", "south_node_sign", "ketu_sign",
                    "uranus_sign", "ceres_sign", "vesta_sign", "pallas_sign",
                    "lilith_sign", "life_path", "chinese_zodiac", "natal_chart",
                ]}}, "required": ["placement"]},
        },
    },
    "get_all_placements": {
        "run": _run_get_all_placements,
        "schema": {
            "name": "get_all_placements",
            "description": ("Получить компактный evidence-пакет всех placement-калькуляторов "
                            "и натальных точек. Используй для полного разбора, но не "
                            "выдумывай поля, скрытые из-за precision."),
            "input_schema": {"type": "object", "properties": {}},
        },
    },
    "get_life_path": {
        "run": _run_get_life_path,
        "schema": {
            "name": "get_life_path",
            "description": "Рассчитать число жизненного пути с трассировкой редукции даты.",
            "input_schema": {"type": "object", "properties": {}},
        },
    },
    "get_chinese_zodiac": {
        "run": _run_get_chinese_zodiac,
        "schema": {
            "name": "get_chinese_zodiac",
            "description": "Рассчитать китайское животное и элемент с учётом китайского Нового года.",
            "input_schema": {"type": "object", "properties": {}},
        },
    },
    "palm_scanner": {
        "run": _run_palm_scanner,
        "schema": {
            "name": "palm_scanner",
            "description": ("Сканер ладони Миры: один вызов возвращает полный экспертный разбор "
                            "последнего vision-чтения — качество кадра, ракурс (раскрытая/согнутая "
                                                         "ладонь), MediaPipe hand geometry (если модель доступна), различимость всех линий (включая линии брака, детей, "

                            "путешествий), холмов и пальцев, тип руки по стихии, знаки, вопросы "
                            "для клиентки и ограничения. Трактуй только видимое evidence по правилам "
                            "хиромантии; без медицинских выводов и предсказаний. Если чтения нет или "
                            "кадр слабый — попроси фото ладони целиком при ровном свете."),
            "input_schema": {"type": "object", "properties": {
                "reading_id": {"type": "integer",
                               "description": "ID чтения, если нужен не последний результат"}}},
        },
    },
    "palm_photo_guide": {
        "run": _run_palm_photo_guide,
        "schema": {
            "name": "palm_photo_guide",
            "description": ("Какие фото ладони нужны и какое доснять: раскрытая ладонь для основных "
                            "линий, согнутая (ребро к камере) — для линий брака, отношений, детей и "
                            "путешествий. Зови, когда кадр не покрывает нужную зону или клиентка "
                            "спрашивает, как фотографировать."),
            "input_schema": {"type": "object", "properties": {}},
        },
    },
    "palm_history": {
        "run": _run_palm_history,
        "schema": {
            "name": "palm_history",
            "description": ("Список прошлых чтений ладони клиентки (id, дата, рука, статус). Зови, "
                            "когда она спрашивает про прошлые разборы или хочет сравнить динамику."),
            "input_schema": {"type": "object", "properties": {
                "limit": {"type": "integer", "description": "Сколько чтений показать, 1-20"}}},
        },
    },
    "get_transits": {
        "run": _run_get_transits,
        "schema": {
            "name": "get_transits",
            "description": ("Небо сегодня: фаза Луны, лунный день, сезон Солнца. "
                            "Зови для прогнозов на день/«как сегодня действовать»."),
            "input_schema": {"type": "object", "properties": {}},
        },
    },
    "get_moon_week": {
        "run": _run_moon_week,
        "schema": {
            "name": "get_moon_week",
            "description": ("Лунный календарь на 7 дней вперёд. Зови, когда клиентка "
                            "выбирает день для решения, поездки, разговора, стрижки."),
            "input_schema": {"type": "object", "properties": {}},
        },
    },
    "get_career_windows": {
        "run": _run_career_windows,
        "schema": {
            "name": "get_career_windows",
            "description": ("Деловые окна на ближайшие недели: когда начинать, "
                            "подписывать, просить повышение, а когда — завершать "
                            "и не принимать решений. Зови для вопросов о карьере, "
                            "переговорах, увольнении, запуске дела."),
            "input_schema": {"type": "object", "properties": {
                "days": {"type": "integer", "description": "Горизонт, 7-30 дней"},
            }},
        },
    },
    "suggest_practice": {
        "run": _run_suggest_practice,
        "schema": {
            "name": "suggest_practice",
            "description": ("Каталог практик (денежные, любовные, энергия) и то, "
                            "что клиентка уже проходит. Зови, когда она спрашивает "
                            "«что мне делать», просит ритуал или практику."),
            "input_schema": {"type": "object", "properties": {
                "category": {"type": "string",
                             "description": "money|love|energy"},
            }},
        },
    },
    "get_matrix": {
        "run": _run_get_matrix,
        "schema": {
            "name": "get_matrix",
            "description": ("Матрица Судьбы клиентки (арканы). Зови для вопросов о "
                            "предназначении, кармических задачах, денежной/любовной линии."),
            "input_schema": {"type": "object", "properties": {}},
        },
    },
    "get_compatibility": {
        "run": _run_compatibility,
        "schema": {
            "name": "get_compatibility",
            "description": ("Совместимость с партнёром по датам рождения. Если дата "
                            "партнёра неизвестна — сначала спроси её у клиентки."),
            "input_schema": {"type": "object", "properties": {
                "partner_birth_date": {"type": "string",
                                       "description": "Дата партнёра YYYY-MM-DD"},
                "relation": {"type": "string",
                             "description": "Тип связи: love|friend|work|family "
                                            "(по умолчанию love)"},
            }, "required": ["partner_birth_date"]},
        },
    },
    "list_partners": {
        "run": _run_list_partners,
        "schema": {
            "name": "list_partners",
            "description": ("Список людей, которых клиентка сохранила (партнёр, коллега, "
                            "подруга) с их датами рождения. Зови, когда она говорит "
                            "«он», «она» без уточнения."),
            "input_schema": {"type": "object", "properties": {}},
        },
    },
    "save_memory": {
        "run": _run_save_memory,
        "schema": {
            "name": "save_memory",
            "description": ("Сохранить важный факт о клиентке (люди, события, чувства, "
                            "цели, даты). Зови всякий раз, когда она делится личным."),
            "input_schema": {"type": "object", "properties": {
                "fact": {"type": "string"},
                "kind": {"type": "string",
                         "description": "person|event|emotion|goal|fact"},
            }, "required": ["fact"]},
        },
    },
    "recall_memory": {
        "run": _run_recall_memory,
        "schema": {
            "name": "recall_memory",
            "description": "Поиск в памяти о клиентке по ключевым словам (люди, темы).",
            "input_schema": {"type": "object", "properties": {
                "query": {"type": "string"}}, "required": ["query"]},
        },
    },
    "recall_diary": {
        "run": _run_recall_diary,
        "schema": {
            "name": "recall_diary",
            "description": ("Последние записи её дневника и стрик. Зови, когда речь о "
                            "самочувствии, динамике, «как у меня дела в последнее время»."),
            "input_schema": {"type": "object", "properties": {}},
        },
    },
}

#: Полный набор инструментов — для главного агента.
TOOLS = [s["schema"] for s in SKILLS.values()]


def tools_for(names: list[str] | tuple[str, ...] | None) -> list[dict]:
    """Схемы только перечисленных скиллов — набор инструментов агента.

    Специализированному агенту лишние инструменты вредят: модель начинает
    отвечать не по своей теме, и «Таролог» уходит в астрологию.
    """
    if not names:
        return list(TOOLS)
    return [SKILLS[n]["schema"] for n in names if n in SKILLS]


async def execute(db, user, name: str, args: dict) -> str:
    skill = SKILLS.get(name)
    if not skill:
        return "неизвестный инструмент"
    try:
        return await skill["run"](db, user, args or {})
    except Exception:  # noqa: BLE001
        log.exception("скилл %s упал", name)
        return "инструмент временно недоступен — не выдумывай данные и продолжи без него"
