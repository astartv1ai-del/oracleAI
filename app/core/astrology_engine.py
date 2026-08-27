"""Improved deterministic engine boundary for OracleAI astrology.

This module owns request normalization and reproducibility metadata. The actual
astronomical backend remains Kerykeion over Swiss Ephemeris in ``astro.py``;
callers must not infer precision from a non-empty clock string or from a city
label. The engine deliberately does not interpret results and never calls an
LLM.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Callable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ENGINE_ADAPTER_VERSION = "oracleai-kerykeion-engine-v2"
_TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


class AstrologyInputError(ValueError):
    """Raised when an astrology request cannot be interpreted safely."""


@dataclass(frozen=True)
class ChartRequest:
    """Canonicalized request passed to the Kerykeion calculator."""

    birth_date: date
    birth_time: tuple[int, int] | None
    original_birth_time: str | None
    city: str | None
    lat: float | None
    lon: float | None
    tz: str | None
    coordinates_known: bool
    time_confirmed: bool
    precision_reason: str

    @property
    def precision(self) -> str:
        if self.time_confirmed and self.coordinates_known:
            return "exact"
        if self.time_confirmed:
            return "time_without_location"
        return "date_only"

    @property
    def angular_data_available(self) -> bool:
        return bool(self.time_confirmed and self.coordinates_known and self.tz)

    @property
    def effective_time(self) -> tuple[int, int]:
        """Technical noon for date snapshots; never reported as birth time."""
        return self.birth_time or (12, 0)

    @property
    def fingerprint(self) -> str:
        payload = {
            "engine_adapter_version": ENGINE_ADAPTER_VERSION,
            "birth_date": self.birth_date.isoformat(),
            "birth_time": self.birth_time,
            "city": self.city,
            "lat": self.lat,
            "lon": self.lon,
            "tz": self.tz,
            "coordinates_known": self.coordinates_known,
            "time_confirmed": self.time_confirmed,
            "precision_reason": self.precision_reason,
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]

    def metadata(self) -> dict[str, Any]:
        return {
            "adapter_version": ENGINE_ADAPTER_VERSION,
            "request_fingerprint": self.fingerprint,
        }


class OracleKerykeionEngine:
    """Request boundary and bounded result cache around the Kerykeion backend."""

    def __init__(self, *, max_cache_entries: int = 256) -> None:
        self.max_cache_entries = max(1, int(max_cache_entries))
        self._cache: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _coordinates_known(lat: float | None, lon: float | None) -> bool:
        if lat is None or lon is None:
            return False
        try:
            lat_value, lon_value = float(lat), float(lon)
        except (TypeError, ValueError):
            return False
        return (
            math.isfinite(lat_value)
            and math.isfinite(lon_value)
            and -90 <= lat_value <= 90
            and -180 <= lon_value <= 180
        )

    @staticmethod
    def _validate_timezone(tz: str | None) -> None:
        if tz is None or tz == "":
            return
        try:
            ZoneInfo(tz)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise AstrologyInputError("Часовой пояс указывается как корректный IANA identifier") from exc

    @staticmethod
    def _parse_time(value: str | None) -> tuple[int, int] | None:
        if value in (None, ""):
            return None
        if not isinstance(value, str) or not _TIME_RE.fullmatch(value):
            raise AstrologyInputError("Время рождения указывается в формате ЧЧ:ММ")
        hour, minute = value.split(":")
        return int(hour), int(minute)

    def normalize(
        self,
        birth_date: str,
        birth_time: str | None,
        city: str | None,
        lat: float | None,
        lon: float | None,
        tz: str | None,
        *,
        time_known: bool | None = None,
    ) -> ChartRequest:
        try:
            parsed_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
        except (TypeError, ValueError) as exc:
            raise AstrologyInputError("Дата рождения указывается в формате YYYY-MM-DD") from exc
        parsed_time = self._parse_time(birth_time)
        self._validate_timezone(tz)
        coordinates_known = self._coordinates_known(lat, lon)
        time_confirmed = bool(parsed_time and time_known is not False and tz)
        precision_reason = (
            "exact" if time_confirmed and coordinates_known else
            "time_without_location" if time_confirmed else
            "date_only_missing_timezone" if parsed_time and not tz else
            "date_only_unconfirmed" if parsed_time else
            "date_only"
        )
        return ChartRequest(
            birth_date=parsed_date,
            birth_time=parsed_time if time_confirmed else None,
            original_birth_time=birth_time,
            city=city,
            lat=lat,
            lon=lon,
            tz=tz,
            coordinates_known=coordinates_known,
            time_confirmed=time_confirmed,
            precision_reason=precision_reason,
        )

    def calculate(
        self,
        request: ChartRequest,
        calculator: Callable[[ChartRequest], dict[str, Any]],
    ) -> dict[str, Any]:
        """Run or retrieve a calculator result and return a defensive copy."""
        cached = self._cache.get(request.fingerprint)
        if cached is not None:
            return copy.deepcopy(cached)
        result = calculator(request)
        if not isinstance(result, dict):
            raise TypeError("astrology calculator must return an object")
        self._cache[request.fingerprint] = copy.deepcopy(result)
        if len(self._cache) > self.max_cache_entries:
            self._cache.pop(next(iter(self._cache)))
        return copy.deepcopy(result)

    def clear_cache(self) -> None:
        self._cache.clear()


ENGINE = OracleKerykeionEngine()
