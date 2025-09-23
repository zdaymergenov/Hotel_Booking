from __future__ import annotations
from functools import reduce
from typing import Any, Callable, Iterable, Mapping, Sequence
import json

from core.domain import (
    Hotel,
    RoomType,
    RatePlan,
    Price,
    Availability,
    Guest,
    CartItem,
)

# Тип оффера: словарь с ключами hotel, room, rate, price_per_night, currency
Offer = Mapping[str, Any]

_DEF_MAP = {
    "hotels": Hotel,
    "room_types": RoomType,
    "rates": RatePlan,
    "prices": Price,
    "availability": Availability,
    "guests": Guest,
}


def _to_tuple(seq: Iterable) -> tuple:
    return tuple(seq)


def load_seed(path: str) -> tuple[
    tuple[Hotel, ...],
    tuple[RoomType, ...],
    tuple[RatePlan, ...],
    tuple[Price, ...],
    tuple[Availability, ...],
    tuple[Guest, ...],
]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    def map_block(key: str, ctor):
        return _to_tuple(map(lambda d: ctor(**d), raw.get(key, [])))

    return (
        map_block("hotels", Hotel),
        map_block("room_types", RoomType),
        map_block("rates", RatePlan),
        map_block("prices", Price),
        map_block("availability", Availability),
        map_block("guests", Guest),
    )


def hold_item(cart: tuple[CartItem, ...], item: CartItem) -> tuple[CartItem, ...]:
    base = tuple(filter(lambda it: it.id != item.id, cart))
    return base + (item,)


def remove_hold(cart: tuple[CartItem, ...], item_id: str) -> tuple[CartItem, ...]:
    return tuple(filter(lambda it: it.id != item_id, cart))


def nightly_sum(
    prices: tuple[Price, ...], checkin: str, checkout: str, rate_id: str
) -> int:
    night_prices = filter(
        lambda p: p.rate_id == rate_id and (p.date >= checkin) and (p.date < checkout),
        prices,
    )
    amounts = map(lambda p: p.amount, night_prices)
    return reduce(lambda acc, x: acc + x, amounts, 0)


# Фильтры для поиска по отелям


def by_city(city: str):
    """Фильтр по городу (частичное совпадение, регистронезависимо)."""
    city_norm = city.strip().lower()
    return lambda offer: city_norm in offer.hotel.city.lower()



def by_capacity(guests: int) -> Callable[[Offer], bool]:
    """Фильтр-замыкание: вместимость номера >= guests."""
    need = max(1, int(guests))
    return lambda offer: int(offer.room_type.capacity) >= need  # доступ к room_type.capacity


def by_features(required: Sequence[str]) -> Callable[[Offer], bool]:
    """Фильтр-замыкание: все требуемые фичи должны встречаться в отеле или номере."""
    req = {str(x).strip().lower() for x in required}

    def pred(offer: Offer) -> bool:
        hotel_feats = {str(x).lower() for x in getattr(offer.hotel, "features", [])}  # доступ к features отеля
        room_feats = {str(x).lower() for x in getattr(offer.room_type, "features", [])}  # доступ к features от RoomType
        return req.issubset(hotel_feats | room_feats)

    return pred


def by_price_range(
    min_amt: int, max_amt: int, currency: str
) -> Callable[[Offer], bool]:
    """Фильтр-замыкание: минимальная/максимальная цена за ночь в нужной валюте."""
    c = str(currency).upper()
    lo, hi = sorted((int(min_amt), int(max_amt)))

    def pred(offer: Offer) -> bool:
        return (
            str(offer.currency).upper() == c
            and lo <= int(offer.price_per_night) <= hi
        )

    return pred



# Хелперы для комбинирования фильтров
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
