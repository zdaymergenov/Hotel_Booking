import json
from pathlib import Path
from types import SimpleNamespace

import streamlit as st

from core.transforms import (
    by_capacity,
    by_city,
    by_features,
    by_price_range,
    combine_all,
    filter_offers,
)


# Ленивая загрузка seed.json из data/
@st.cache_data(show_spinner=False)
def load_seed(path: str = "data/seed.json") -> dict:
    p = Path(path)
    if not p.exists():
        st.warning("data/seed.json не найден — покажу демо-данные")
        demo = {
            "hotels": [
                {
                    "id": "h1",
                    "name": "City Hotel",
                    "stars": 3,
                    "city": "Алматы",
                    "features": ["wifi", "parking"],
                },
                {
                    "id": "h2",
                    "name": "Beach Resort",
                    "stars": 4,
                    "city": "Астана",
                    "features": ["spa", "pool"],
                },
            ],
            "room_types": [
                {
                    "id": "r1",
                    "hotel_id": "h1",
                    "name": "Standard",
                    "capacity": 2,
                    "beds": ["queen"],
                    "features": ["ac"],
                },
                {
                    "id": "r2",
                    "hotel_id": "h2",
                    "name": "Family",
                    "capacity": 4,
                    "beds": ["queen", "twin"],
                    "features": ["balcony"],
                },
            ],
            "rates": [
                {
                    "id": "rp1",
                    "hotel_id": "h1",
                    "room_type_id": "r1",
                    "title": "BAR",
                    "meal": "RO",
                    "refundable": True,
                    "cancel_before_days": 3,
                },
                {
                    "id": "rp2",
                    "hotel_id": "h2",
                    "room_type_id": "r2",
                    "title": "BAR",
                    "meal": "BB",
                    "refundable": False,
                    "cancel_before_days": None,
                },
            ],
            "prices": [
                {
                    "id": "p1",
                    "rate_id": "rp1",
                    "date": "2025-10-01",
                    "amount": 25000,
                    "currency": "KZT",
                },
                {
                    "id": "p2",
                    "rate_id": "rp2",
                    "date": "2025-10-01",
                    "amount": 48000,
                    "currency": "KZT",
                },
            ],
        }
        return demo
    return json.loads(p.read_text(encoding="utf-8"))


def build_offers(seed: dict) -> tuple[dict, ...]:
    hotels = {h["id"]: h for h in seed.get("hotels", [])}
    rooms = [rt for rt in seed.get("room_types", [])]
    rates = [rp for rp in seed.get("rates", [])]
    prices = seed.get("prices", [])

    # Индекс минимальной цены за ночь по rate_id
    min_price_by_rate: dict[str, dict] = {}
    for pr in prices:
        rid = pr["rate_id"]
        cur = min_price_by_rate.get(rid)
        if cur is None or int(pr["amount"]) < cur["amount"]:
            min_price_by_rate[rid] = {
                "amount": int(pr["amount"]),
                "currency": pr["currency"],
            }

    offers: list[dict] = []
    for rate in rates:
        hotel = hotels.get(rate["hotel_id"]) or {}
        room = next((r for r in rooms if r["id"] == rate["room_type_id"]), None)
        mp = min_price_by_rate.get(rate["id"]) or {"amount": 0, "currency": "KZT"}
        offers.append(
            {
                "hotel": SimpleNamespace(**hotel),
                "room": SimpleNamespace(**(room or {})),
                "rate": SimpleNamespace(**rate),
                "price_per_night": mp["amount"],
                "currency": mp["currency"],
            }
        )
    return tuple(offers)


st.set_page_config(page_title="Hotel Search — Лаба 2", layout="wide")

seed = load_seed()
offers = build_offers(seed)

st.title("Лаба 2: Поиск и фильтры (SPA demo)")

with st.sidebar:
    st.header("Фильтры")
    cities = sorted(
        {o["hotel"].city for o in offers if getattr(o["hotel"], "city", None)}
    )
    city = st.selectbox("Город", options=["(любой)"] + cities)
    guests = st.number_input("Гостей", min_value=1, max_value=8, value=2)
    all_feats = sorted(
        {
            *(f for o in offers for f in getattr(o["hotel"], "features", [])),
            *(f for o in offers for f in getattr(o["room"], "features", [])),
        }
    )
    feats = st.multiselect("Фичи", options=all_feats)
    min_amt = st.number_input("Бюджет от, тыйын/коп.", min_value=0, value=0, step=1000)
    max_amt = st.number_input(
        "Бюджет до, тыйын/коп.", min_value=0, value=1000000, step=1000
    )
    currency = st.selectbox("Валюта", options=sorted({o["currency"] for o in offers}))

preds = []
if city and city != "(любой)":
    preds.append(by_city(city))
preds.append(by_capacity(int(guests)))
if feats:
    preds.append(by_features(tuple(feats)))
preds.append(by_price_range(int(min_amt), int(max_amt), currency))

predicate = combine_all(*preds)
filtered = filter_offers(offers, predicate)

st.subheader(f"Найдено предложений: {len(filtered)}")
for o in filtered:
    st.markdown(
        f"**{o['hotel'].name}** — {o['room'].name} — {o['rate'].title} | "
        f"{o['price_per_night']} {o['currency']} / ночь"
    )
