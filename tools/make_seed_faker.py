from __future__ import annotations
import json, random
from pathlib import Path
from datetime import date, timedelta
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

START = date(2025, 10, 1)
DAYS = 60

MEALS = ["RO", "BB", "HB"]
BEDS = ["single", "double", "queen", "king", "twin"]
FEATURES = ["wifi", "pool", "spa", "gym", "parking", "bar", "pets"]

hotels, room_types, rates, prices, availability, guests = [], [], [], [], [], []

# 5–8 отелей
for hi in range(1, random.randint(5, 8) + 1):
    hid = f"h{hi}"
    hotels.append(
        {
            "id": hid,
            "name": fake.company() + " Hotel",
            "stars": random.choice([3, 4, 5]),
            "city": fake.city(),
            "features": random.sample(FEATURES, k=random.randint(2, 4)),
        }
    )
    for rti in range(1, 5):  # 4 room types/отель
        rtid = f"rt{hi}_{rti}"
        room_types.append(
            {
                "id": rtid,
                "hotel_id": hid,
                "name": fake.word().capitalize() + " Room",
                "capacity": random.choice([1, 2, 3, 4]),
                "beds": random.sample(BEDS, k=1),
                "features": random.sample(FEATURES, k=random.randint(1, 3)),
            }
        )
        for ri in range(1, 2 + 1):  # 2 тарифа/тип
            rid = f"r{hi}_{rti}_{ri}"
            refundable = random.choice([True, False])
            cancel_days = random.choice([None, 3, 7]) if refundable else None
            rates.append(
                {
                    "id": rid,
                    "hotel_id": hid,
                    "room_type_id": rtid,
                    "title": random.choice(["Standard", "Non-Refundable", "Flexible"]),
                    "meal": random.choice(MEALS),
                    "refundable": refundable,
                    "cancel_before_days": cancel_days,
                }
            )

# Цены
for r in rates:
    base = random.randint(15000, 45000)
    for d in range(DAYS):
        day = START + timedelta(days=d)
        prices.append(
            {
                "id": f"p_{r['id']}_{d}",
                "rate_id": r["id"],
                "date": str(day),
                "amount": base + random.randint(-2000, 4000),
                "currency": "KZT",
            }
        )

# Доступность
for rt in room_types:
    for d in range(DAYS):
        day = START + timedelta(days=d)
        availability.append(
            {
                "id": f"a_{rt['id']}_{d}",
                "room_type_id": rt["id"],
                "date": str(day),
                "available": random.randint(2, 6),
            }
        )

# 50 гостей
for gi in range(1, 51):
    guests.append(
        {
            "id": f"g{gi}",
            "name": fake.name(),
            "email": fake.email(),
        }
    )

seed = {
    "hotels": hotels,
    "room_types": room_types,
    "rates": rates,
    "prices": prices,
    "availability": availability,
    "guests": guests,
}

Path("data").mkdir(parents=True, exist_ok=True)
with open("data/seed.json", "w", encoding="utf-8") as f:
    json.dump(seed, f, ensure_ascii=False, indent=2)

print("✅ seed.json создан → data/seed.json")
