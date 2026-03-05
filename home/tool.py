import math
import requests

def toado(diachi):
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={diachi}, Vietnam"
    headers = {'User-Agent': 'MyDjangoApp/1.0'}
    response = requests.get(url, headers=headers).json()
    if response:
        lat = float(response[0]['lat'])
        lon = float(response[0]['lon'])
        return lat, lon
    return None, None

    

def tinhkhoangcach(lat1, lon1, lat2, lon2):
    R = 6371

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    khoangcach = R * c
    return round(khoangcach, 2)

def cuahanggannhat(latkh, lonkh, cuahang):
    cua_hang = cuahang[0]
    km = tinhkhoangcach(latkh, lonkh, cua_hang.lat, cua_hang.lon)
    for ch in cuahang:
        khoangcach = tinhkhoangcach(latkh, lonkh, ch.lat, ch.lon)
        if khoangcach < km:
            km = khoangcach
            cua_hang = ch
    return cua_hang, km