from __future__ import annotations

from typing import Any, Callable, Iterable, Mapping, Sequence

# Тип оффера: словарь с ключами hotel, room, rate, price_per_night, currency
Offer = Mapping[str, Any]


def by_city(city: str) -> Callable[[Offer], bool]:
    """Фильтр-замыкание: оставить офферы по городу отеля (ровно).
    Ожидает offer["hotel"].city (str).
    """
    city_norm = city.strip().lower()
    return lambda offer: str(offer["hotel"].city).lower() == city_norm


def by_capacity(guests: int) -> Callable[[Offer], bool]:
    """Фильтр-замыкание: вместимость номера >= guests.
    Ожидает offer["room"].capacity (int).
    """
    need = max(1, int(guests))
    return lambda offer: int(offer["room"].capacity) >= need


def by_features(required: Sequence[str]) -> Callable[[Offer], bool]:
    """Фильтр-замыкание: все требуемые фичи должны встречаться в отеле или номере.
    Ожидает offer["hotel"].features и offer["room"].features (итерируемые строки).
    """
    req = {str(x).strip().lower() for x in required}

    def pred(offer: Offer) -> bool:
        hotel_feats = {str(x).lower() for x in getattr(offer["hotel"], "features", [])}
        room_feats = {str(x).lower() for x in getattr(offer["room"], "features", [])}
        return req.issubset(hotel_feats | room_feats)

    return pred


def by_price_range(
    min_amt: int, max_amt: int, currency: str
) -> Callable[[Offer], bool]:
    """Фильтр-замыкание: минимальная/максимальная цена за ночь в нужной валюте.
    Ожидает offer["price_per_night"] (int, в тыйын/копейках) и offer["currency"].
    """
    c = str(currency).upper()
    lo, hi = sorted((int(min_amt), int(max_amt)))

    def pred(offer: Offer) -> bool:
        return (
            str(offer["currency"]).upper() == c
            and lo <= int(offer["price_per_night"]) <= hi
        )

    return pred


# Хелперы композиции фильтров
def combine_all(*preds: Callable[[Offer], bool]) -> Callable[[Offer], bool]:
    """AND-комбинация произвольного числа предикатов."""

    def _pred(x: Offer) -> bool:
        for p in preds:
            if not p(x):
                return False
        return True

    return _pred


def filter_offers(
    offers: Iterable[Offer], predicate: Callable[[Offer], bool]
) -> tuple[Offer, ...]:
    """Применить фильтр к коллекции офферов. Возвращает tuple (иммутабельность на выходе)."""
    return tuple(o for o in offers if predicate(o))
