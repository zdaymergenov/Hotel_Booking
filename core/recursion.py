from __future__ import annotations

from datetime import date, timedelta
from typing import NamedTuple

# Поддержка импорта RatePlan из core.domain, но оставим fallback для автономного запуска
try:  # pragma: no cover - исключительно на случай отсутствия проекта Лабы 1
    from .domain import RatePlan  # type: ignore
except Exception:  # pragma: no cover

    class RatePlan(NamedTuple):  # минимальный макет
        id: str
        hotel_id: str
        room_type_id: str
        title: str
        meal: str
        refundable: bool
        cancel_before_days: int | None


def split_date_range(checkin: str, checkout: str) -> tuple[str, ...]:
    """Рекурсивно развернуть интервал [checkin, checkout) в список ночей (ISO-даты).
    Если checkout <= checkin — вернуть пустой tuple.
    """
    d1 = date.fromisoformat(checkin)
    d2 = date.fromisoformat(checkout)
    if d2 <= d1:
        return tuple()

    out: list[str] = []

    def rec(cur: date) -> None:
        if cur >= d2:
            return  # база рекурсии
        out.append(cur.isoformat())
        rec(cur + timedelta(days=1))  # шаг рекурсии

    rec(d1)
    return tuple(out)


def build_policy_tree(rate: RatePlan, horizon_days: int = 30) -> tuple[dict, ...]:
    """Рекурсивно «развернуть» политику отмены по дням до заезда на horizon_days.
    Нода: {day_before, can_cancel}.
    Логика: если refundable=False — отмена запрещена всегда; иначе — разрешена
    только за cancel_before_days (если задано) дней и более до заезда.
    """
    out: list[dict] = []

    def rec(day: int) -> None:
        if day < 0:
            return
        can = True
        if not rate.refundable:
            can = False
        elif rate.cancel_before_days is not None and day < int(rate.cancel_before_days):
            can = False
        out.append({"day_before": day, "can_cancel": can})
        rec(day - 1)

    rec(int(horizon_days))
    return tuple(out)
