import json
import os
import requests
from django.http import JsonResponse
from django.shortcuts import render
from .gis.spatial_query import find_nearby_stores, filter_by_district


# ====== CONFIG ======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "stores.json")

ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImY5ZjYwZGVjZjY0YzQwNmVhYjAxZjMxY2QxMzM0NTE3IiwiaCI6Im11cm11cjY0In0="   # ⚠ Đưa key thật của bạn vào đây


# ===============================
# PAGE VIEW
# ===============================
def map_view(request):
    return render(request, "maptool/map.html")


# ===============================
# API: LOAD ALL STORES
# ===============================
def all_stores_api(request):
    try:
        lat = request.GET.get("lat")
        lng = request.GET.get("lng")

        with open(DATA_PATH, "r", encoding="utf-8") as f:
            stores = json.load(f)

        # Nếu có vị trí user → tính khoảng cách
        if lat and lng:
            lat = float(lat)
            lng = float(lng)

            results = find_nearby_stores(lat, lng, stores, radius=100)
            return JsonResponse({"stores": results})

        # Nếu chưa lấy vị trí → trả bình thường
        return JsonResponse({"stores": stores})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# ===============================
# API: NEARBY STORES
# ===============================
def nearby_api(request):
    try:
        lat = request.GET.get("lat")
        lng = request.GET.get("lng")
        radius = request.GET.get("radius", 3)

        if not lat or not lng:
            return JsonResponse({"error": "Missing coordinates"}, status=400)

        lat = float(lat)
        lng = float(lng)
        radius = float(radius)

        with open(DATA_PATH, "r", encoding="utf-8") as f:
            stores = json.load(f)

        results = find_nearby_stores(lat, lng, stores, radius)

        return JsonResponse({"stores": results})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ===============================
# API: FILTER BY DISTRICT
# ===============================
def district_api(request):
    try:
        district = request.GET.get("district", "")

        with open(DATA_PATH, "r", encoding="utf-8") as f:
            stores = json.load(f)

        results = filter_by_district(stores, district)

        return JsonResponse({"stores": results})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ===============================
# API: ROUTE (OPENROUTESERVICE)
# ===============================
def route_api(request):
    try:
        start_lat = request.GET.get("start_lat")
        start_lng = request.GET.get("start_lng")
        end_lat = request.GET.get("end_lat")
        end_lng = request.GET.get("end_lng")

        if not all([start_lat, start_lng, end_lat, end_lng]):
            return JsonResponse({"error": "Missing parameters"}, status=400)

        start_lat = float(start_lat)
        start_lng = float(start_lng)
        end_lat = float(end_lat)
        end_lng = float(end_lng)

        url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"

        headers = {
            "Authorization": ORS_API_KEY,
            "Content-Type": "application/json"
        }

        body = {
            "coordinates": [
                [start_lng, start_lat],
                [end_lng, end_lat]
            ]
        }

        response = requests.post(
            url,
            json=body,
            headers=headers,
            timeout=10
        )

        data = response.json()

        if response.status_code != 200:
            return JsonResponse({
                "error": "ORS API error",
                "detail": data
            }, status=400)

        # Debug in terminal
        print("ORS RESPONSE:", data)

        if "features" not in data:
            return JsonResponse({
                "error": "Invalid route response",
                "detail": data
            }, status=400)

        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
