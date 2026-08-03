"""FastAPI: Mini App, админ-панель и API.

Запуск: `uvicorn app.api.main:app --port 8080`

Процессов два — бот и это приложение. Они делят один файл SQLite (режим WAL) и
общий код правил в `app/services`, поэтому поведение в Telegram и в Mini App
совпадает по определению, а не по случайности.
"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ..config import settings
from ..core import sentry as sentry
from .deps import close_db, get_db
from .routers import ROUTERS

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("oracle.api")

ROOT = Path(__file__).resolve().parent.parent.parent
MINIAPP_DIR = ROOT / "miniapp"
ADMIN_DIR = ROOT / "admin"
WEB_DIR = ROOT / "web"                 # публичный лендинг и SEO-файлы (G36)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Подключаемся к БД на старте, чтобы миграции прошли до первого запроса."""
    sentry.init()
    db = await get_db()
    from ..data.session import healthcheck
    state = await healthcheck(db)
    log.info("API готов. БД: %s таблиц, журнал %s, пользователей %s",
             state["schema_tables"], state["journal_mode"], state["users"])
    if settings.dev_mode:
        log.warning("DEV_MODE=1 — вход по ?dev_user=<id> без подписи Telegram. "
                    "На боевом сервере поставь DEV_MODE=0")
    yield
    await close_db()


app = FastAPI(title="Оракул API", version="1.0.0", lifespan=lifespan,
              docs_url="/api/docs" if settings.dev_mode else None,
              redoc_url=None, openapi_url="/api/openapi.json"
              if settings.dev_mode else None)


@app.middleware("http")
async def access_log(request: Request, call_next):
    """Лог запросов и защита от утечки внутренних ошибок клиенту."""
    started = time.monotonic()
    try:
        response = await call_next(request)
    except Exception as e:
        # Пользователю — тёплый 500, диагностика — в Sentry: молча терять падение
        # нельзя, а показывать стек клиентке — тоже.
        sentry.capture_exception(e)
        log.exception("необработанная ошибка на %s %s", request.method,
                      request.url.path)
        return JSONResponse(
            {"detail": "Связь со звёздами прервалась… попробуй ещё раз 🌙"},
            status_code=500)
    took = (time.monotonic() - started) * 1000
    if took > 2000 or response.status_code >= 500:
        log.warning("%s %s → %s за %.0f мс", request.method, request.url.path,
                    response.status_code, took)
    response.headers["X-Response-Time"] = f"{took:.0f}ms"
    # Mini App грузится во вебвью Telegram; запрет фрейминга посторонними
    # источниками не мешает ему и закрывает clickjacking на админку
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    # Тем же origin живут и Mini App, и панель — скрипты только отсюда и с
    # https://telegram.org (SDK вебвью). Swagger (dev) грузится со сторонних
    # CDN и с inline-стилями, поэтому в DEV_MODE строгий CSP не вешаем (G24).
    if not settings.dev_mode:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' https://telegram.org; "
            "style-src 'self'; img-src 'self' data:; connect-src 'self'; "
            "base-uri 'self'; form-action 'self'; frame-ancestors 'self'")
    _cache_control(request.url.path, response)
    return response


for router in ROUTERS:
    app.include_router(router)


#: Ассеты, которые можно коротко кешировать. Имена не содержат хеша контента
#: (app.js, а не app.abc123.js), поэтому TTL скромный: устаревшая копия живёт
#: не дольше задеплоенного часа. HTML и API — всегда no-cache.
_ASSET_EXTS = {"js", "css", "png", "jpg", "jpeg", "webp", "gif", "svg",
               "woff", "woff2", "ico", "txt"}


def _cache_control(path: str, response) -> None:
    if path.startswith("/static/") or path.startswith("/admin/static/"):
        response.headers["Cache-Control"] = "public, max-age=3600"
    elif path.count("/") <= 1 and path.rsplit(".", 1)[-1].lower() in _ASSET_EXTS:
        response.headers["Cache-Control"] = "public, max-age=3600"
    else:
        response.headers["Cache-Control"] = "no-cache"


# ──────────────────────────── статика Mini App ────────────────────────────────

def _file(directory: Path, name: str) -> FileResponse:
    path = directory / name
    if not path.is_file():
        return JSONResponse({"detail": "не найдено"}, status_code=404)
    return FileResponse(path)


@app.get("/", include_in_schema=False)
async def index():
    return _file(MINIAPP_DIR, "index.html")


@app.get("/admin", include_in_schema=False)
@app.get("/admin/", include_in_schema=False)
async def admin_index():
    """Панель открывается кнопкой из бота — вход по подписи Telegram."""
    return _file(ADMIN_DIR, "index.html")


if MINIAPP_DIR.is_dir():
    # монтируем как статику: отдельные обработчики на каждый файл пришлось бы
    # править при добавлении картинки или шрифта
    app.mount("/static", StaticFiles(directory=str(MINIAPP_DIR)), name="static")
if ADMIN_DIR.is_dir():
    app.mount("/admin/static", StaticFiles(directory=str(ADMIN_DIR)),
              name="admin-static")


@app.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    return _file(WEB_DIR, "robots.txt")


@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml():
    return _file(WEB_DIR, "sitemap.xml")


@app.get("/landing", include_in_schema=False)
async def landing():
    """Публичный лендинг для поиска и шаринга ссылок (не Mini App)."""
    return _file(WEB_DIR, "landing.html")


@app.get("/{filename}", include_in_schema=False)
async def miniapp_asset(filename: str):
    """Файлы Mini App по короткому пути (`/app.js`, `/styles.css`).

    Проверка на разделители пути обязательна: без неё `GET /..%2F.env` отдал бы
    файл настроек с токенами.
    """
    if "/" in filename or "\\" in filename or filename.startswith("."):
        return JSONResponse({"detail": "не найдено"}, status_code=404)
    return _file(MINIAPP_DIR, filename)
