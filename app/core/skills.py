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
from . import astro, memory, tarot
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


# ---------------------------------------------------------------- skills

async def _run_draw_tarot(db, user, args) -> str:
    n = max(1, min(int(args.get("n", 3) or 3), 12))
    spread_code = str(args.get("spread", "") or "")
    item = tarot.spread(spread_code) if spread_code else None
    positions = item["positions"] if item and spread_code in tarot.SPREADS else None
    if positions:
        n = len(positions)
    cards = tarot.draw(n)
    title = item["title"] if item else "свободный"
    return (f"{await guide(db, 'tarot')}\n\nРасклад: {title}\n"
            f"Карты:\n{tarot.cards_text(cards, positions)}")


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
    days = max(7, min(int(args.get("days", 14) or 14), 30))
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
    relation = str(args.get("relation", "love") or "love").strip()
    try:
        datetime.strptime(partner, "%Y-%m-%d")
    except ValueError:
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
    fact = str(args.get("fact", "") or "").strip()
    if not fact:
        return "нечего сохранять"
    saved = await memory.remember(db, user["tg_id"], fact,
                                  kind=str(args.get("kind", "fact") or "fact"))
    return "сохранено" if saved else "уже знаю это — усилила важность"


async def _run_recall_memory(db, user, args) -> str:
    if not bool(user["memory_enabled"]):
        return "память выключена — сохранённые факты не используются"
    query = str(args.get("query", "") or "")
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


SKILLS: dict[str, dict] = {
    "draw_tarot": {
        "run": _run_draw_tarot,
        "schema": {
            "name": "draw_tarot",
            "description": ("Вытянуть карты Таро (реальный случайный выбор из 78 карт). "
                            "Зови, когда нужен расклад или клиентка просит «что говорят карты»."),
            "input_schema": {"type": "object", "properties": {
                "n": {"type": "integer", "description": "Число карт 1-12"},
                "spread": {"type": "string",
                           "description": "Код расклада: one, three, love, choice, "
                                          "money, career, work, celtic, year"},
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
            "description": ("Каталог практик и мантр (мантры, денежные, любовные, "
                            "энергия) и то, что клиентка уже проходит. Зови, когда "
                            "она спрашивает «что мне делать», просит ритуал, "
                            "практику или мантру."),
            "input_schema": {"type": "object", "properties": {
                "category": {"type": "string",
                             "description": "mantra|money|love|energy"},
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
    except Exception as e:  # noqa: BLE001
        log.warning("скилл %s упал: %s", name, e)
        return f"ошибка инструмента: {e}"
