"""FastAPI: Mini App, админ-панель и API.

Запуск: `uvicorn app.api.main:app --port 8080`

Процессов два — бот и это приложение. Они делят один файл SQLite (режим WAL) и
общий код правил в `app/services`, поэтому поведение в Telegram и в Mini App
совпадает по определению, а не по случайности.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from ..config import settings
from ..core import sentry as sentry
from ..core.observability import (
    configure_logging,
    log_event,
    new_request_id,
    reset_request_id,
    set_request_id,
)
from .deps import close_db, get_db
from .routers import ROUTERS

configure_logging(level=settings.log_level, log_file=settings.log_file)
log = logging.getLogger("oracle.api")

HTTP_REQUESTS = Counter(
    "oracleai_http_requests_total",
    "Total HTTP requests handled by the API.",
    ("method", "status"),
)
HTTP_LATENCY = Histogram(
    "oracleai_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ("method",),
)

ROOT = Path(__file__).resolve().parent.parent.parent
MINIAPP_DIR = ROOT / "miniapp"
ADMIN_DIR = ROOT / "admin"
WEB_DIR = ROOT / "web"                 # публичный лендинг и SEO-файлы (G36)


def _validate_production_config() -> None:
    """Fail closed before serving an unauthenticated or misdirected app."""
    app_env = os.getenv("APP_ENV", "").lower()
    if app_env in {"dev", "test"}:
        return
    missing = []
    if app_env != "production":
        missing.append("APP_ENV должен быть production")
    if settings.dev_mode:
        missing.append("DEV_MODE должен быть выключен")
    if not settings.bot_token:
        missing.append("BOT_TOKEN")
    if not settings.admin_id:
        missing.append("ADMIN_ID")
    if not settings.webapp_url:
        missing.append("WEBAPP_URL")
    else:
        parsed = urlsplit(settings.webapp_url)
        if (parsed.scheme != "https" or not parsed.netloc or
                parsed.username or parsed.password):
            missing.append("WEBAPP_URL должен быть HTTPS URL без учётных данных")
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        missing.append("DATABASE_URL")
    elif "postgresql" not in database_url.lower():
        missing.append("DATABASE_URL должен указывать на PostgreSQL")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "").strip()
    if not postgres_password or postgres_password.lower() in {
            "oracle", "change_me", "password", "postgres"}:
        missing.append("POSTGRES_PASSWORD должен быть задан и не быть шаблонным")
    if os.getenv("CELERY_ENABLED", "0") == "1" and not os.getenv("REDIS_URL", "").strip():
        missing.append("REDIS_URL при CELERY_ENABLED=1")
    if not settings.release_id or settings.release_id == "local":
        missing.append("RELEASE_ID")
    if missing:
        raise RuntimeError("production-конфигурация не готова: " + ", ".join(missing))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Подключаемся к БД на старте, чтобы миграции прошли до первого запроса."""
    # DEV_MODE=1 отключает подпись Telegram (?dev_user=<id>) — это только для
    # разработки. Забытая на бою единица открывает API всем подряд, поэтому
    # запуск падает, если режим включён не в dev-окружении (APP_ENV=dev).
    if settings.dev_mode and os.getenv("APP_ENV", "") != "dev":
        raise RuntimeError(
            "DEV_MODE=1 включает вход по ?dev_user=<id> БЕЗ подписи Telegram. "
            "Допустимо только в dev: выстави APP_ENV=dev либо выключи DEV_MODE=0")
    _validate_production_config()
    sentry.init()
    db = await get_db()
    from ..data.session import healthcheck
    state = await healthcheck(db)
    log_event(
        log, logging.INFO, "api_ready", "API готов",
        operation="startup", release_id=settings.release_id,
        schema_tables=state["schema_tables"], journal_mode=state["journal_mode"],
    )
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
    """JSONL-лог запросов и защита от утечки внутренних ошибок клиенту."""
    started = time.monotonic()
    rid = new_request_id()
    token = set_request_id(rid)
    try:
        try:
            response = await call_next(request)
        except Exception as e:
            # Пользователю — тёплый 500, диагностика — в Sentry: молча терять
            # падение нельзя, а показывать стек клиентке — тоже.
            sentry.capture_exception(e)
            log.exception(
                "необработанная ошибка API",
                extra={
                    "event": "http_5xx",
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": 500,
                },
            )
            response = JSONResponse(
                {"detail": "Связь со звёздами прервалась… попробуй ещё раз 🌙"},
                status_code=500)
        took = (time.monotonic() - started) * 1000
        HTTP_REQUESTS.labels(request.method, str(response.status_code)).inc()
        HTTP_LATENCY.labels(request.method).observe(took / 1000)
        if took > 2000 or response.status_code >= 500:
            level = logging.ERROR if response.status_code >= 500 else logging.WARNING
            log_event(
                log, level, "http_request", "медленный или ошибочный запрос",
                method=request.method, path=request.url.path,
                status_code=response.status_code, latency_ms=round(took),
            )
        response.headers["X-Response-Time"] = f"{took:.0f}ms"
        response.headers["X-Request-ID"] = rid
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
                # Static templates use data-dependent inline style attributes; keep
                # scripts strict while allowing those layout tokens to render.
                "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                "font-src 'self'; connect-src 'self'; media-src 'self'; "
                "object-src 'none'; base-uri 'self'; form-action 'self'; "
                "frame-ancestors 'self'")
        _cache_control(request.url.path, response)
        return response
    finally:
        reset_request_id(token)


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    """Prometheus metrics; Caddy denies this path on the public edge."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


for router in ROUTERS:
    app.include_router(router)


#: Source assets keep a short TTL because their names are not content-hashed;
#: production bundles use the immutable branch below. HTML and API are no-cache.
_ASSET_EXTS = {"js", "css", "png", "jpg", "jpeg", "webp", "gif", "svg",
               "woff", "woff2", "ico", "txt"}


def _cache_control(path: str, response) -> None:
    if path == "/api/chart/image":
        # Authenticated raster charts may be reused by the same private webview,
        # but must never become a shared/proxy cache object.
        response.headers.setdefault("Cache-Control", "private, max-age=3600, must-revalidate")
    elif path.startswith("/static/dist/") and re.search(r"\.[0-9a-f]{12}\.min\.(?:js|css)$", path):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif path.startswith("/static/") or path.startswith("/admin/static/"):
        response.headers["Cache-Control"] = "public, max-age=3600"
    elif path.count("/") <= 1 and path.rsplit(".", 1)[-1].lower() in _ASSET_EXTS:
        response.headers["Cache-Control"] = "public, max-age=3600"
    else:
        response.headers.setdefault("Cache-Control", "no-cache")


# ──────────────────────────── статика Mini App ────────────────────────────────

def _file(directory: Path, name: str) -> FileResponse:
    path = directory / name
    if not path.is_file():
        return JSONResponse({"detail": "не найдено"}, status_code=404)
    return FileResponse(path)


def _miniapp_index_body() -> str:
    body = (MINIAPP_DIR / "index.html").read_text(encoding="utf-8")
    # Development keeps source modules visible by default. CI/browser QA may opt
    # into the production bundle with BUNDLE_ASSETS=1 without weakening auth.
    if settings.dev_mode and os.getenv("BUNDLE_ASSETS") != "1":
        return body
    manifest_path = MINIAPP_DIR / "dist" / "manifest.json"
    if not manifest_path.is_file():
        return body
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        css = manifest["css"]
        js = manifest["js"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        log.exception("invalid Mini App asset manifest")
        return body
    body = re.sub(r'/static/styles\.css\?v=\d+', f'/static/dist/{css}', body)
    body = re.sub(r'\n<script src="/static/js/[^"?]+\?v=\d+"></script>', '', body)
    return body.replace('</body>', f'<script src="/static/dist/{js}"></script>\n</body>')


@app.get("/", include_in_schema=False)
async def index():
    path = MINIAPP_DIR / "index.html"
    if not path.is_file():
        return JSONResponse({"detail": "не найдено"}, status_code=404)
    return HTMLResponse(_miniapp_index_body())


@app.get("/admin", include_in_schema=False)
@app.get("/admin/", include_in_schema=False)
async def admin_index():
    """Панель открывается кнопкой из бота — вход по подписи Telegram."""
    path = ADMIN_DIR / "index.html"
    if not path.is_file():
        return JSONResponse({"detail": "не найдено"}, status_code=404)
    # JS/CSS живут в CDN-кеше час, поэтому имя выдачи получает версию от их
    # mtime. После любого деплоя HTML no-cache подхватит новые ассеты сразу.
    asset_version = str(max(
        (ADMIN_DIR / "admin.js").stat().st_mtime_ns,
        (ADMIN_DIR / "admin.css").stat().st_mtime_ns,
    ))
    return HTMLResponse(path.read_text(encoding="utf-8").replace(
        "__ADMIN_ASSET_VERSION__", asset_version))


if MINIAPP_DIR.is_dir():
    # монтируем как статику: отдельные обработчики на каждый файл пришлось бы
    # править при добавлении картинки или шрифта
    app.mount("/static", StaticFiles(directory=str(MINIAPP_DIR)), name="static")
if ADMIN_DIR.is_dir():
    app.mount("/admin/static", StaticFiles(directory=str(ADMIN_DIR)),
              name="admin-static")
if WEB_DIR.is_dir():
    # Только публичные стили и изображения лендинга; HTML отдаётся отдельными
    # маршрутами выше, поэтому страницы не становятся случайно browseable.
    app.mount("/public", StaticFiles(directory=str(WEB_DIR)), name="public-static")


def _public_base(request: Request) -> str:
    # Production startup requires WEBAPP_URL, so Host headers cannot poison
    # canonical, robots or sitemap URLs. A request-derived fallback is dev-only.
    return settings.webapp_url or (str(request.base_url).rstrip("/")
                                   if settings.dev_mode else "")


def _public_template(name: str, request: Request) -> HTMLResponse:
    path = WEB_DIR / name
    if not path.is_file():
        return HTMLResponse("Страница не найдена", status_code=404)
    body = path.read_text(encoding="utf-8").replace("__PUBLIC_BASE_URL__", _public_base(request))
    return HTMLResponse(body)


@app.get("/robots.txt", include_in_schema=False)
async def robots_txt(request: Request):
    body = ("User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /api\nDisallow: /static\n\n"
            f"Sitemap: {_public_base(request)}/sitemap.xml\n")
    return Response(body, media_type="text/plain")


@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap_xml(request: Request):
    base = _public_base(request)
    body = ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
            "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
            f"  <url><loc>{base}/landing</loc></url>\n"
            f"  <url><loc>{base}/landing/en</loc></url>\n"
            f"  <url><loc>{base}/privacy</loc></url>\n"
            f"  <url><loc>{base}/terms</loc></url>\n"
            f"  <url><loc>{base}/privacy/en</loc></url>\n"
            f"  <url><loc>{base}/terms/en</loc></url>\n"
            "</urlset>\n")
    return Response(body, media_type="application/xml")


@app.get("/landing", include_in_schema=False)
async def landing(request: Request):
    """Публичный русскоязычный лендинг для поиска и шаринга ссылок."""
    return _public_template("landing.html", request)


@app.get("/landing/en", include_in_schema=False)
async def landing_en(request: Request):
    """Англоязычная версия публичного лендинга."""
    return _public_template("landing-en.html", request)


@app.get("/privacy", include_in_schema=False)
async def privacy(request: Request):
    return _public_template("privacy.html", request)


@app.get("/privacy/en", include_in_schema=False)
async def privacy_en(request: Request):
    return _public_template("privacy-en.html", request)


@app.get("/terms", include_in_schema=False)
async def terms(request: Request):
    return _public_template("terms.html", request)


@app.get("/terms/en", include_in_schema=False)
async def terms_en(request: Request):
    return _public_template("terms-en.html", request)


@app.get("/{filename}", include_in_schema=False)
async def miniapp_asset(filename: str):
    """Файлы Mini App по короткому пути (`/app.js`, `/styles.css`).

    Проверка на разделители пути обязательна: без неё `GET /..%2F.env` отдал бы
    файл настроек с токенами.
    """
    if "/" in filename or "\\" in filename or filename.startswith("."):
        return JSONResponse({"detail": "не найдено"}, status_code=404)
    return _file(MINIAPP_DIR, filename)
