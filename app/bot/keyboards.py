"""Клавиатуры бота.

Правило раскладки: главное действие — всегда первой строкой и во всю ширину,
остальное — парами. Кнопки, ведущие к оплате, отделены от бесплатных, чтобы не
нажимались случайно.
"""
from __future__ import annotations

from urllib.parse import quote

from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           WebAppInfo)

from ..config import settings

CB_MENU = "menu"


def _webapp_button(text: str, path: str = "") -> InlineKeyboardButton | None:
    """Кнопка Mini App. Без https-адреса Telegram её просто не примет."""
    if not settings.webapp_url:
        return None
    url = settings.webapp_url + path
    return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=url))


def main_menu(*, is_admin: bool = False) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    app_btn = _webapp_button("✨ Открыть Оракула", "/")
    if app_btn:
        rows.append([app_btn])
    rows += [
        [InlineKeyboardButton(text="💬 Спросить Оракула", callback_data="ask")],
        [
            InlineKeyboardButton(text="🎴 Расклад Таро", callback_data="tarot"),
            InlineKeyboardButton(text="🌌 Моя карта", callback_data="chart"),
        ],
        [InlineKeyboardButton(text="✋ Мира · Проводник ладони", callback_data="palm")],
        [
            InlineKeyboardButton(text="🔢 Матрица Судьбы", callback_data="matrix"),
            InlineKeyboardButton(text="📖 Дневник", callback_data="diary"),
        ],
        [
            InlineKeyboardButton(text="🌅 Прогноз дня", callback_data="today"),
            InlineKeyboardButton(text="💞 Совместимость", callback_data="compat"),
        ],
        [
            InlineKeyboardButton(text="🕉 Практики", callback_data="practices"),
            InlineKeyboardButton(text="🧭 Карьера", callback_data="career"),
        ],
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
            InlineKeyboardButton(text="💎 Лавка", callback_data="shop"),
        ],
    ]
    if is_admin:
        admin_btn = _webapp_button("📊 Панель управления", "/admin")
        rows.append([admin_btn] if admin_btn
                    else [InlineKeyboardButton(text="📊 Статистика",
                                               callback_data="admin_stats")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def age_gate_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = ("I am 16+", "Close") if lang == "en" else ("Мне уже 16+", "Закрыть")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels[0], callback_data="age:confirm")],
        [InlineKeyboardButton(text=labels[1], callback_data="age:decline")],
    ])


def gender_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Выбор формы обращения в онбординге; пропуск сохраняет нейтральный язык."""
    labels = (
        ("Female ♀", "Male ♂", "Skip")
        if lang == "en" else ("Женский ♀", "Мужской ♂", "Пропустить")
    )
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels[0], callback_data="gender:f"),
         InlineKeyboardButton(text=labels[1], callback_data="gender:m")],
        [InlineKeyboardButton(text=labels[2], callback_data="gender:skip")],
    ])


def personas_kb(personas: list[dict]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{p['emoji']} {p['title']}",
                              callback_data=f"persona:{p['code']}")]
        for p in personas
    ])


def agents_kb(agents: list[dict]) -> InlineKeyboardMarkup:
    """Выбор собеседника: у каждого агента своя специализация."""
    rows = [[InlineKeyboardButton(text=f"{a['emoji']} {a['title']}",
                                  callback_data=f"agent:{a['code']}")]
            for a in agents]
    rows.append([InlineKeyboardButton(text="← Меню", callback_data=CB_MENU)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def spreads_kb(spreads: list[dict]) -> InlineKeyboardMarkup:
    """Расклады: входящие в тариф сверху, платные — с ценой на кнопке."""
    rows = []
    for item in spreads:
        if item["tier"] == "included":
            label = f"{item['emoji']} {item['title']}"
        elif item["owned"]:
            label = f"{item['emoji']} {item['title']} · открыт ✓"
        else:
            price = (f"⭐{item['price_stars']}" if item["price_stars"]
                     else f"✦{item['price_crystals']}")
            label = f"{item['emoji']} {item['title']} · {price}"
        rows.append([InlineKeyboardButton(text=label[:60],
                                          callback_data=f"spread:{item['code']}")])
    rows.append([InlineKeyboardButton(text="← Меню", callback_data=CB_MENU)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def spread_offer_kb(item: dict) -> InlineKeyboardMarkup:
    """Расклад не входит в тариф — предлагаем купить его или подписку."""
    rows = []
    if item.get("sku") and item.get("price_stars"):
        rows.append([InlineKeyboardButton(
            text=f"⭐ Купить за {item['price_stars']} Stars",
            callback_data=f"buy_sku:{item['sku']}")])
    if item.get("sku") and item.get("price_crystals"):
        rows.append([InlineKeyboardButton(
            text=f"✦ Открыть за {item['price_crystals']} Кристаллов",
            callback_data=f"buy_crystals:{item['sku']}")])
    # Подписка на витринах скрыта (этап «только Кристаллы»); хендлер `plans`
    # оставлен — вернём кнопкой, когда решим снова продавать.
    rows.append([InlineKeyboardButton(text="← К раскладам", callback_data="tarot")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def limit_kb(cost: int, *, has_crystals: bool, lang: str = "ru") -> InlineKeyboardMarkup:
    """Лимит исчерпан. Порядок кнопок = порядок выгоды для пользователя."""
    en = lang == "en"
    rows = []
    if has_crystals:
        rows.append([InlineKeyboardButton(
            text=(f"🔮 Emergency question · ✦{cost}" if en
                  else f"🔮 Экстренный вопрос · ✦{cost}"), callback_data="emergency")])
    rows += [
        [InlineKeyboardButton(text=("💎 Buy Crystals" if en else "💎 Купить Кристаллы"),
                              callback_data="shop_crystals")],
        [InlineKeyboardButton(text=("← Menu" if en else "← Меню"), callback_data=CB_MENU)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def shop_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎴 Одиночные расклады", callback_data="shop_spreads")],
        [InlineKeyboardButton(text="📜 Большие разборы", callback_data="shop_reports")],
        [InlineKeyboardButton(text="💬 Дополнительные вопросы", callback_data="shop_questions")],
        [InlineKeyboardButton(text="✦ Кристаллы", callback_data="shop_crystals")],
        [InlineKeyboardButton(text="🎟 Ввести промокод", callback_data="promo")],
        [InlineKeyboardButton(text="← Меню", callback_data=CB_MENU)],
    ])


def plans_kb(plans: list[dict], current: str) -> InlineKeyboardMarkup:
    rows = []
    for plan in plans:
        if not plan.get("price_stars"):
            continue
        mark = " ✓" if plan["code"] == current else ""
        badge = f" · {plan['badge']}" if plan.get("badge") else ""
        rows.append([InlineKeyboardButton(
            text=f"{plan['title']} — ⭐{plan['price_stars']}{badge}{mark}"[:60],
            callback_data=f"buy_plan:{plan['code']}")])
    rows.append([InlineKeyboardButton(text="← Лавка", callback_data="shop")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def products_kb(products: list[dict], *, back: str = "shop",
                crypto_skus: tuple = ()) -> InlineKeyboardMarkup:
    """Витрина товаров: Stars и Кристаллы — двумя кнопками, чтобы не путать.

    Для пакетов Кристаллов добавляется третья кнопка — крипта (Crypto Pay):
    без юрлица это единственный канал с картой/USDT и низкой комиссией.
    """
    rows = []
    for product in products:
        line = []
        if product["price_stars"]:
            line.append(InlineKeyboardButton(
                text=f"⭐{product['price_stars']}",
                callback_data=f"buy_sku:{product['sku']}"))
        if product["price_crystals"]:
            line.append(InlineKeyboardButton(
                text=f"✦{product['price_crystals']}",
                callback_data=f"buy_crystals:{product['sku']}"))
        if product["kind"] == "crystals" and product["sku"] in crypto_skus:
            line.append(InlineKeyboardButton(
                text="₿ Криптой", callback_data=f"buy_crypto:{product['sku']}"))
        rows.append([InlineKeyboardButton(text=product["title"][:60],
                                          callback_data=f"product:{product['sku']}")])
        if line:
            rows.append(line)
    rows.append([InlineKeyboardButton(text="← Лавка", callback_data=back)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def profile_kb(*, push_on: bool, sub_active: bool) -> InlineKeyboardMarkup:
    rows = []
    # «Продлить доступ» скрыт вместе с подписками (этап «только Кристаллы»).
    rows += [
        [InlineKeyboardButton(text="💎 Лавка", callback_data="shop")],
        [InlineKeyboardButton(text="🌟 Пригласить близкого", callback_data="invite")],
        [InlineKeyboardButton(
            text=f"🌅 Утренний прогноз: {'вкл ✅' if push_on else 'выкл ☑️'}",
            callback_data="toggle_push")],
        [InlineKeyboardButton(text="🔮 Сменить образ Оракула",
                              callback_data="change_persona")],
        [InlineKeyboardButton(text="📜 Мои разборы", callback_data="my_reports")],
        [InlineKeyboardButton(text="← Меню", callback_data=CB_MENU)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def share_kb(link: str, text: str, *, label: str = "💌 Поделиться") -> InlineKeyboardMarkup:
    share_url = "https://t.me/share/url?url=" + quote(link) + "&text=" + quote(text)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, url=share_url)],
        [InlineKeyboardButton(text="← Меню", callback_data=CB_MENU)],
    ])


def reading_kb(reading_id: int, share_url: str, *,
               with_card: bool = True) -> InlineKeyboardMarkup:
    """Под раскладом: отметка «сбылось» (обратная связь) и шеринг (виральность).

    Картинка для сторис — отдельной кнопкой: в этой нише делятся скриншотом
    расклада, а не ссылкой, и красивая карточка работает как реклама сама.
    """
    rows = [[
        InlineKeyboardButton(text="✅ Сбылось",
                             callback_data=f"outcome:{reading_id}:came_true"),
        InlineKeyboardButton(text="🤔 Частично",
                             callback_data=f"outcome:{reading_id}:partly"),
    ]]
    if with_card:
        rows.append([InlineKeyboardButton(text="🖼 Картинка для сторис",
                                          callback_data=f"card:{reading_id}")])
    rows += [
        [InlineKeyboardButton(text="💌 Поделиться", url=share_url)],
        [InlineKeyboardButton(text="🎴 Ещё расклад", callback_data="tarot")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def practices_kb(items: list[dict], categories: list[dict],
                 *, active: str | None = None) -> InlineKeyboardMarkup:
    """Практики: сначала идущие (к ним возвращаются), потом каталог по разделам."""
    rows = []
    running = [p for p in items if p["started"] and not p["finished"]]
    for item in running[:4]:
        rows.append([InlineKeyboardButton(
            text=f"{item['emoji']} {item['title']} · день "
                 f"{item['day_index']}/{item['days']}"[:60],
            callback_data=f"practice:{item['code']}")])
    if running:
        rows.append([InlineKeyboardButton(text="— каталог —",
                                          callback_data="practices")])
    line = []
    for cat in categories:
        mark = " ✓" if cat["code"] == active else ""
        line.append(InlineKeyboardButton(
            text=f"{cat['emoji']} {cat['title']}{mark}"[:30],
            callback_data=f"practice_cat:{cat['code']}"))
        if len(line) == 2:
            rows.append(line)
            line = []
    if line:
        rows.append(line)
    for item in items:
        if item["started"] and not item["finished"]:
            continue
        mark = " ✓" if item["finished"] else ""
        rows.append([InlineKeyboardButton(
            text=f"{item['emoji']} {item['title']} · {item['days']} дн.{mark}"[:60],
            callback_data=f"practice:{item['code']}")])
    rows.append([InlineKeyboardButton(text="← Меню", callback_data=CB_MENU)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def practice_kb(item: dict) -> InlineKeyboardMarkup:
    """Карточка практики: главное действие зависит от того, идёт ли она."""
    rows = []
    if item["finished"]:
        rows.append([InlineKeyboardButton(text="🔁 Пройти заново",
                                          callback_data=f"practice_start:{item['code']}")])
    elif item["started"]:
        rows.append([InlineKeyboardButton(
            text=f"✅ Отметить день {item['day_index'] + 1}",
            callback_data=f"practice_done:{item['code']}")])
        rows.append([InlineKeyboardButton(text="⏹ Остановить",
                                          callback_data=f"practice_stop:{item['code']}")])
    else:
        rows.append([InlineKeyboardButton(
            text=f"▶️ Начать · {item['days']} дней",
            callback_data=f"practice_start:{item['code']}")])
    rows.append([InlineKeyboardButton(text="← К практикам",
                                      callback_data="practices")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def career_kb() -> InlineKeyboardMarkup:
    """Карьерный раздел: расклады, деловые окна и большой разбор."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧭 Расклад «Карьера и путь»",
                              callback_data="spread:career")],
        [InlineKeyboardButton(text="⚖️ Расклад «Проблемы на работе»",
                              callback_data="spread:work")],
        [InlineKeyboardButton(text="📅 Деловые окна на 2 недели",
                              callback_data="career_windows")],
        [InlineKeyboardButton(text="📜 Полный разбор карьеры",
                              callback_data="shop_reports")],
        [InlineKeyboardButton(text="← Меню", callback_data=CB_MENU)],
    ])


def back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Меню", callback_data=CB_MENU)]
    ])


def report_kb(reports: list[dict]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=f"📜 {r['title']}"[:60],
                                  callback_data=f"report:{r['kind']}:{r['period'] or ''}")]
            for r in reports]
    rows.append([InlineKeyboardButton(text="← Профиль", callback_data="profile")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
