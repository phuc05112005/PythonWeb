import math


def haversine_distance(lat1, lon1, lat2, lon2):

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


def calculate_delivery_fee(distance):

    base_fee = 15000
    extra_fee = max(0, distance - 3) * 5000

    return int(base_fee + extra_fee)
