import streamlit as st
from statistics import mean

from core.transforms import load_seed, nightly_sum, filter_offers, combine_all, by_city, by_capacity, by_price_range
from core.domain import Offer, Hotel, RoomType, RatePlan, Price  # добавили Offer

st.set_page_config(page_title="Hotel Booking — Overview", layout="centered")

st.title("Hotel Booking — Overview (Lab 1 & 2)")

(hotels, room_types, rates, prices, availability, guests) = load_seed("data/seed.json")

col1, col2, col3 = st.columns(3)
col1.metric("# Hotels", len(hotels))
col2.metric("# Room Types", len(room_types))
col3.metric("# Rates", len(rates))

st.divider()
price_days = len({p.date for p in prices})
st.metric("Days in price calendar", price_days)

st.subheader("Average price by city & stars (rough)")
hotels_by_id = {h.id: h for h in hotels}
rates_by_id = {r.id: r for r in rates}

first_price_by_rate = {}
for p in sorted(prices, key=lambda x: (x.rate_id, x.date)):
    first_price_by_rate.setdefault(p.rate_id, p.amount)

city_to_amounts = {}
for rate_id, amt in first_price_by_rate.items():
    hotel = hotels_by_id[rates_by_id[rate_id].hotel_id]
    city_to_amounts.setdefault(hotel.city, []).append(amt)
for city, amts in city_to_amounts.items():
    st.write(f"**{city}** — {int(mean(amts))} (avg minor units)")

stars_to_amounts = {}
for rate_id, amt in first_price_by_rate.items():
    hotel = hotels_by_id[rates_by_id[rate_id].hotel_id]
    stars_to_amounts.setdefault(hotel.stars, []).append(amt)
for stars, amts in sorted(stars_to_amounts.items()):
    st.write(f"⭐ x{stars} — {int(mean(amts))} (avg minor units)")

st.divider()
st.subheader("Nightly sum demo")
rate_opt = st.selectbox("Pick a rate", options=[r.id for r in rates])
checkin = st.text_input("Check-in (YYYY-MM-DD)", value="2025-10-01")
checkout = st.text_input("Check-out (YYYY-MM-DD)", value="2025-10-05")
if st.button("Calculate"):
    total = nightly_sum(prices, checkin, checkout, rate_opt)
    st.success(f"Total for period: {total} (minor units)")

st.divider()
st.subheader("Filtered offers demo")

# ==== СОЗДАЁМ OFFERS ====
room_types_by_id = {rt.id: rt for rt in room_types}
first_price_by_rate_obj = {}
for p in sorted(prices, key=lambda x: (x.rate_id, x.date)):
    first_price_by_rate_obj.setdefault(p.rate_id, p)

offers = []
for rate in rates:
    hotel = hotels_by_id[rate.hotel_id]
    room_type = room_types_by_id[rate.room_type_id]
    price = first_price_by_rate_obj.get(rate.id)
    if price:
        offers.append(
            Offer(
                hotel=hotel,
                room_type=room_type,
                rate=rate,
                price_per_night=price.amount,
                currency=price.currency,
            )
        )

# ==== ФИЛЬТРЫ ====
city = st.text_input("Enter city", "")
capacity = st.number_input("Enter number of guests", min_value=1, max_value=10, value=1)
min_price = st.number_input("Min price", value=0)
max_price = st.number_input("Max price", value=100000)
currency = st.text_input("Currency", "KZT")

filters = []
if city:
    filters.append(by_city(city))
filters.append(by_capacity(capacity))
filters.append(by_price_range(min_price, max_price, currency))

combined_filter = combine_all(*filters)
filtered_offers = filter_offers(offers, combined_filter)

st.subheader(f"Found {len(filtered_offers)} offers")
for offer in filtered_offers:
    st.write(
        f"{offer.hotel.name} — {offer.room_type.name} — "
        f"{offer.rate.title} | {offer.price_per_night} {offer.currency} / night"
    )
