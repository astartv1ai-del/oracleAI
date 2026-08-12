"""Конфигурация приложения (.env).

Здесь только то, что нельзя менять на ходу: секреты, адреса, режим работы.
Всё продуктовое (цены, лимиты, тексты, фиче-флаги) живёт в БД и правится в
админ-панели без деплоя — см. `app/data/seed.py` и `app/repo/content.py`.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DATA_DIR = Path(os.getenv("DATA_DIR") or (ROOT / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "") or default)
    except ValueError:
        return default


#: Не `frozen=True`: тесты и админские сценарии подменяют отдельные поля на
#: живом объекте (`monkeypatch.setattr(settings, ...)`), а хеширование настроек
#: нигде не используется.
@dataclass
class Settings:
    # ── Telegram ──
    bot_token: str = os.getenv("BOT_TOKEN", "")
    admin_id: int = _int("ADMIN_ID", 0)
    webapp_url: str = os.getenv("WEBAPP_URL", "").rstrip("/")

    # ── LLM ──
    llm_provider: str = os.getenv("LLM_PROVIDER", "auto")  # auto|custom|anthropic|openai|off
    anthropic_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    openai_key: str = os.getenv("OPENAI_API_KEY", "")
    custom_base_url: str = os.getenv("CUSTOM_LLM_BASE_URL", "").rstrip("/")
    custom_api_key: str = os.getenv("CUSTOM_LLM_API_KEY", "")
    custom_model_main: str = os.getenv("CUSTOM_LLM_MODEL", "")
    custom_model_lite: str = os.getenv("CUSTOM_LLM_MODEL_LITE",
                                       os.getenv("CUSTOM_LLM_MODEL", ""))
    anthropic_main: str = os.getenv("ANTHROPIC_MODEL_MAIN", "claude-sonnet-5")
    anthropic_lite: str = os.getenv("ANTHROPIC_MODEL_LITE", "claude-haiku-4-5-20251001")
    openai_main: str = os.getenv("OPENAI_MODEL_MAIN", "gpt-4o")
    openai_lite: str = os.getenv("OPENAI_MODEL_LITE", "gpt-4o-mini")

    # ── мониторинг (G31): пусто = Sentry выключен ──
    sentry_dsn: str = os.getenv("SENTRY_DSN", "")

    # ── защита LLM от всплеска: сколько вызовов одновременно и в минуту ──
    llm_max_concurrency: int = _int("LLM_MAX_CONCURRENCY", 8)
    llm_rate_per_min: int = _int("LLM_RATE_PER_MIN", 240)

    # ── память по смыслу (необязательна: без неё работает поиск по словам) ──
    embed_model: str = os.getenv("EMBED_MODEL", "text-embedding-3-small")
    embed_via_custom: bool = os.getenv("EMBED_VIA_CUSTOM", "0") == "1"

    # ── озвучка прогнозов (тариф «Консьерж») ──
    tts_model: str = os.getenv("TTS_MODEL", "gpt-4o-mini-tts")
    tts_voice: str = os.getenv("TTS_VOICE", "shimmer")

    # ── каналы-спутники: по каналу на знак, {sign} — латинский код знака ──
    horoscope_channels: str = os.getenv("HOROSCOPE_CHANNELS", "")

    # ── web-оплата (Paddle / LemonSqueezy): основной чек мимо комиссии Stars ──
    paddle_webhook_secret: str = os.getenv("PADDLE_WEBHOOK_SECRET", "")
    paddle_api_key: str = os.getenv("PADDLE_API_KEY", "")
    paddle_api_url: str = os.getenv("PADDLE_API_URL", "https://api.paddle.com").rstrip("/")
    paddle_checkout_url: str = os.getenv("PADDLE_CHECKOUT_URL", "").rstrip("/")
    # `vip:pri_...,basic:pri_...` — never derive a provider price from client input.
    paddle_price_ids: str = os.getenv("PADDLE_PRICE_IDS", "")

    # ── окружение и наблюдаемость ──
    app_env: str = os.getenv("APP_ENV", "dev").lower()
    dev_mode: bool = os.getenv("DEV_MODE", "0") == "1"
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_file: str = os.getenv("LOG_FILE", "")
    release_id: str = os.getenv("RELEASE_ID", "local")
    db_path: str = os.getenv("DB_PATH") or str(DATA_DIR / "oracle.db")
    public_url: str = os.getenv("PUBLIC_URL", "").rstrip("/")

    # ── продуктовые значения по умолчанию ──
    # Рабочие значения берутся из таблицы `settings`; эти нужны, пока БД пуста
    # (первый старт, тесты, офлайн-скрипты).
    daily_questions: int = 3
    trial_days: int = _int("TRIAL_DAYS", 30)
    crystals_start: int = _int("TRIAL_CRYSTALS", 30)
    crystals_emergency_cost: int = 20
    ref_bonus: int = 15
    vip_stars_price: int = 1300
    crystal_packs: tuple = ((100, 550), (250, 1150), (600, 2250))

    def paddle_price_id(self, plan_code: str) -> str:
        for item in self.paddle_price_ids.split(","):
            code, sep, price_id = item.partition(":")
            if sep and code.strip() == plan_code:
                return price_id.strip()
        return ""

    @property
    def custom_ready(self) -> bool:
        return bool(self.custom_base_url and self.custom_model_main)

    @property
    def provider_chain(self) -> tuple:
        """Порядок LLM-провайдеров: основной + резервные.

        Цепочка — не роскошь: локальный сервер падает, у облачного кончаются
        кредиты, и без резерва клиентка получала бы «сервис недоступен» вместо
        ответа. Последний уровень — офлайн-режим, он в `core/agents/runtime.py`.
        """
        available = []
        if self.custom_ready:
            available.append("custom")
        if self.anthropic_key:
            available.append("anthropic")
        if self.openai_key:
            available.append("openai")
        if self.llm_provider in ("custom", "anthropic", "openai"):
            if self.llm_provider in available:
                return tuple([self.llm_provider] +
                             [p for p in available if p != self.llm_provider])
            return tuple()
        if self.llm_provider == "off":
            return tuple()
        return tuple(available)

    @property
    def provider(self) -> str:
        chain = self.provider_chain
        return chain[0] if chain else "off"

    @property
    def llm_enabled(self) -> bool:
        return self.provider != "off"

    @property
    def ready(self) -> list[str]:
        """Чего не хватает для боевого запуска — печатается при старте бота."""
        problems = []
        if not self.bot_token:
            problems.append("BOT_TOKEN не задан")
        if not self.admin_id:
            problems.append("ADMIN_ID не задан — в админ-панель будет не войти")
        if self.dev_mode:
            problems.append("DEV_MODE=1 — вход в API без подписи Telegram")
        if not self.webapp_url:
            problems.append("WEBAPP_URL пуст — кнопка Mini App не появится")
        if not self.llm_enabled:
            problems.append("нет ключей LLM — работает офлайн-режим")
        return problems


settings = Settings()
