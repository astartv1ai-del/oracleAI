from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ...core import palm as palm_core
from ...core import placements
from ...core.geo import resolve_city_async
from ..common.validation import parse_birth_date
from ..deps import current_user, get_db, rate_limit

router = APIRouter(prefix="/api", tags=["placements"])


class PlacementIn(BaseModel):
    placement: str = Field(min_length=2, max_length=40)
    birth_date: str | None = None
    birth_time: str | None = Field(default=None, max_length=5)
    birth_city: str | None = Field(default=None, max_length=60)


@router.get("/placements")
async def placement_catalog():
    return {
        "calculators": [
            {"code": code, "label": meta["label"],
             "scope": meta["scope"]}
            for code, meta in placements.PLACEMENT_META.items()
        ] + [
            {"code": "life_path", "label": "Число жизненного пути",
             "scope": "symbolic themes of purpose and recurring choices"},
            {"code": "chinese_zodiac", "label": "Китайский зодиакальный знак",
             "scope": "temperament and habitual way of moving through life"},
            {"code": "natal_chart", "label": "Натальная карта",
             "scope": "full sky map with precision metadata"},
        ],
        "palm": {"code": "palm_reading", "label": "Сканер чтения по ладони",
                  "raw_image_stored": False},
    }


@router.post("/placements/calculate", dependencies=[Depends(rate_limit("write"))])
async def calculate_placement(item: PlacementIn, user=Depends(current_user),
                              db=Depends(get_db)):
    supplied = item.model_fields_set
    birth_date = parse_birth_date(item.birth_date) if item.birth_date else user["birth_date"]
    if not birth_date:
        raise HTTPException(400, "укажи дату рождения")
    city = (item.birth_city if "birth_city" in supplied else user["birth_city"]) or None
    birth_time = (item.birth_time if "birth_time" in supplied else user["birth_time"]) or None
    time_known = bool(birth_time) if "birth_time" in supplied else bool(user["birth_time_known"])
    lat = user["birth_lat"] if city == user["birth_city"] else None
    lon = user["birth_lon"] if city == user["birth_city"] else None
    tz = user["tz"] if city == user["birth_city"] else None
    if city and city != user["birth_city"]:
        lat, lon, tz = await resolve_city_async(city, db)
    try:
        result = placements.calculate_placement(
            item.placement, birth_date, birth_time, city, lat, lon, tz,
            time_known=time_known)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True, "result": result}


@router.get("/palm")
async def list_palm(user=Depends(current_user), db=Depends(get_db)):
    from ...repo import palm as palm_repo
    return {"items": await palm_repo.list_readings(db, user["tg_id"], limit=20),
            "raw_image_stored": False}


@router.post("/palm", dependencies=[Depends(rate_limit("llm"))])
async def analyze_palm(request: Request, user=Depends(current_user), db=Depends(get_db)):
    content_type = (request.headers.get("content-type") or "").split(";", 1)[0].lower()
    if content_type not in palm_core.ALLOWED_MIME:
        raise HTTPException(415, "отправь изображение JPEG, PNG или WebP")
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            declared_size = int(content_length)
        except (TypeError, ValueError) as exc:
            raise HTTPException(400, "некорректный размер изображения") from exc
        if declared_size < 0:
            raise HTTPException(400, "некорректный размер изображения")
        if declared_size > palm_core.MAX_IMAGE_BYTES:
            raise HTTPException(413, "фото слишком большое; максимум 8 МБ")
    image = await request.body()
    try:
        result = await palm_core.analyze_and_save(db, user, image)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, "не удалось завершить чтение ладони; попробуй ещё раз") from exc
    return result


@router.get("/palm/{reading_id}")
async def get_palm(reading_id: int, user=Depends(current_user), db=Depends(get_db)):
    result = await palm_core.get(db, user, reading_id)
    if not result:
        raise HTTPException(404, "чтение ладони не найдено")
    return result


@router.delete("/palm/{reading_id}", dependencies=[Depends(rate_limit("write"))])
async def delete_palm(reading_id: int, user=Depends(current_user), db=Depends(get_db)):
    from ...repo import palm as palm_repo
    if not await palm_repo.delete_reading(db, reading_id, user["tg_id"]):
        raise HTTPException(404, "чтение ладони не найдено")
    return {"ok": True}
