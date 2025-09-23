from core.domain import CartItem, Price
from core.transforms import load_seed, hold_item, remove_hold, nightly_sum


def test_load_seed_ok():
    hotels, room_types, rates, prices, availability, guests = load_seed("data/seed.json")
    assert len(hotels) >= 5
    assert len(room_types) >= 20
    assert len(rates) >= 40
    assert len(prices) >= 60


def test_hold_item_add_and_immutability():
    cart = ()
    item = CartItem(
        id="it1",
        hotel_id="h1",
        room_type_id="rt1",
        rate_id="r1",
        checkin="2025-10-01",
        checkout="2025-10-03",
        guests=2,
    )
    new_cart = hold_item(cart, item)
    assert cart == ()
    assert new_cart[-1] == item


def test_hold_item_replace_by_id():
    a = CartItem("it1", "h1", "rt1", "r1", "2025-10-01", "2025-10-02", 2)
    b = CartItem("it1", "h1", "rt1", "r1", "2025-10-03", "2025-10-05", 2)
    out = hold_item((a,), b)
    assert len(out) == 1 and out[0] == b


def test_remove_hold():
    a = CartItem("a", "h1", "rt1", "r1", "2025-10-01", "2025-10-02", 1)
    b = CartItem("b", "h1", "rt1", "r1", "2025-10-02", "2025-10-03", 1)
    cart = (a, b)
    out = remove_hold(cart, "a")
    assert out == (b,)
    assert cart == (a, b)


def test_nightly_sum_simple():
    prices = (
        Price("p1", "r1", "2025-10-01", 1000, "KZT"),
        Price("p2", "r1", "2025-10-02", 1000, "KZT"),
        Price("p3", "r1", "2025-10-03", 2000, "KZT"),
        Price("p4", "r2", "2025-10-01", 9999, "KZT"),
    )
    total = nightly_sum(prices, "2025-10-01", "2025-10-03", "r1")
    assert total == 2000
