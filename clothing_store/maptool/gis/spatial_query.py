import math


# ===============================
# HAVERSINE DISTANCE (km)
# ===============================
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius (km)

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


# ===============================
# FIND NEARBY STORES
# ===============================
def find_nearby_stores(user_lat, user_lng, stores, radius):

    results = []

    for store in stores:
        distance = calculate_distance(
            user_lat,
            user_lng,
            store["lat"],
            store["lng"],
        )

        if distance <= radius:
            store_copy = store.copy()

            store_copy["distance"] = round(distance, 2)
            store_copy["shipping_fee"] = int(distance * 15000)

            results.append(store_copy)

    return results


# ===============================
# FILTER BY DISTRICT
# ===============================
def filter_by_district(stores, district):
    return [
        store for store in stores
        if store["district"].lower() == district.lower()
    ]
