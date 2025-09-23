from types import SimpleNamespace

from core.recursion import RatePlan, build_policy_tree, split_date_range
from core.transforms import (
    by_capacity,
    by_city,
    by_features,
    by_price_range,
    combine_all,
    filter_offers,
)


def _mk_offer(
    city="Алматы",
    cap=2,
    feats_h=("wifi",),
    feats_r=("ac",),
    price=25000,
    cur="KZT",
):
    hotel = SimpleNamespace(id="h", name="H", city=city, features=feats_h)
    room = SimpleNamespace(
        id="r", hotel_id="h", name="R", capacity=cap, features=feats_r
    )
    rate = SimpleNamespace(
        id="rp",
        hotel_id="h",
        room_type_id="r",
        title="BAR",
        meal="RO",
        refundable=True,
        cancel_before_days=3,
    )
    return {
        "hotel": hotel,
        "room": room,
        "rate": rate,
        "price_per_night": price,
        "currency": cur,
    }


def test_split_date_range_basic():
    days = split_date_range("2025-10-01", "2025-10-04")
    assert days == ("2025-10-01", "2025-10-02", "2025-10-03")


def test_split_date_range_empty_on_invalid():
    assert split_date_range("2025-10-05", "2025-10-05") == tuple()
    assert split_date_range("2025-10-06", "2025-10-05") == tuple()


def test_by_city_and_capacity():
    offers = (
        _mk_offer(city="Алматы", cap=2),
        _mk_offer(city="Астана", cap=4),
    )
    pred = combine_all(by_city("Астана"), by_capacity(3))
    res = filter_offers(offers, pred)
    assert len(res) == 1 and res[0]["hotel"].city == "Астана"


def test_by_features_union_of_hotel_and_room():
    offers = (_mk_offer(feats_h=("wifi",), feats_r=("balcony",)),)
    pred = by_features(("wifi", "balcony"))
    assert filter_offers(offers, pred)


def test_by_price_range_and_currency():
    offers = (
        _mk_offer(price=30000, cur="KZT"),
        _mk_offer(price=50000, cur="KZT"),
    )
    pred = by_price_range(25000, 40000, "KZT")
    res = filter_offers(offers, pred)
    assert len(res) == 1 and res[0]["price_per_night"] == 30000


def test_build_policy_tree_refundable_window():
    rp = RatePlan("rp", "h", "r", "BAR", "RO", True, 3)
    tree = build_policy_tree(rp, horizon_days=5)
    denied = {n["day_before"] for n in tree if not n["can_cancel"]}
    assert denied == {0, 1, 2}
