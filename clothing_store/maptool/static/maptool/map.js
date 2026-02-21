let map = L.map('map').setView([10.7769, 106.7009], 12);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

let userLat = null;
let userLng = null;
let userMarker = null;
let storeMarkers = [];
let routeLayer = null;
let bufferLayer = null;

// ================= CLEAR =================
function clearStoreMarkers() {
    storeMarkers.forEach(marker => map.removeLayer(marker));
    storeMarkers = [];
}

function clearRoute() {
    if (routeLayer) {
        map.removeLayer(routeLayer);
        routeLayer = null;
    }
}

function clearBuffer() {
    if (bufferLayer) {
        map.removeLayer(bufferLayer);
        bufferLayer = null;
    }
}


// ================= ADD STORE MARKER =================
function addStoreMarker(store) {

    const storeIcon = L.icon({
        iconUrl: "/static/maptool/icons/adidas.png", 
        iconSize: [40, 40],
        iconAnchor: [20, 40],
        popupAnchor: [0, -35]
    });
    const marker = L.marker([store.lat, store.lng], { icon: storeIcon }).addTo(map);
    let popupContent = `
        <div style="min-width:260px;font-size:14px">
            <h3 style="margin-bottom:5px">${store.name}</h3>
            <div><b>Địa chỉ:</b> ${store.address || "Không có thông tin"}</div>
    `;

    // Nếu có khoảng cách (API nearby)
    if (store.distance !== undefined) {

        popupContent += `
            <hr style="margin:6px 0">
            <div><b>Khoảng cách:</b> ${store.distance} km</div>
            <div style="color:#d9534f;font-weight:bold">
                Phí giao: ${store.shipping_fee.toLocaleString("vi-VN")} đ
            </div>
        `;
    }

    popupContent += `
            <div style="margin-top:8px;text-align:center">
                <button onclick="drawRoute(${store.lat}, ${store.lng})"
                        style="padding:6px 12px;
                               background:black;
                               color:white;
                               border:none;
                               border-radius:6px;
                               cursor:pointer;">
                    Chỉ đường
                </button>
            </div>
        </div>
    `;

    marker.bindPopup(popupContent);

    storeMarkers.push(marker);
}


// ================= LOAD ALL STORES =================
function loadStores() {

    let url = "/map/api/all/";

    if (userLat && userLng) {
        url += `?lat=${userLat}&lng=${userLng}`;
    }

    fetch(url)
        .then(res => res.json())
        .then(data => {

            clearStoreMarkers();
            clearBuffer();
            clearRoute();

            data.stores.forEach(store => {
                addStoreMarker(store);
            });
        });
}


// ================= GET CURRENT LOCATION =================
function getCurrentLocation() {

    navigator.geolocation.getCurrentPosition(pos => {

        userLat = pos.coords.latitude;
        userLng = pos.coords.longitude;

        if (userMarker) map.removeLayer(userMarker);

        const userIcon = L.icon({
            iconUrl: "/static/maptool/icons/location.png",
            iconSize: [35, 35],
            iconAnchor: [17, 35],
            popupAnchor: [0, -30]
        });

        userMarker = L.marker([userLat, userLng], { icon: userIcon })
            .addTo(map)
            .bindPopup("📍 Vị trí của bạn")
            .openPopup();

        map.setView([userLat, userLng], 14);

    }, err => alert(err.message));
}


// ================= NEARBY =================
function showNearbyShops(radius) {

    if (!userLat) {
        alert("Vui lòng bấm My Location trước!");
        return;
    }

    clearBuffer();
    clearRoute();

    bufferLayer = L.circle([userLat, userLng], {
        radius: radius * 1000,
        color: 'blue',
        fillOpacity: 0.1
    }).addTo(map);

    fetch(`/map/api/nearby/?lat=${userLat}&lng=${userLng}&radius=${radius}`)
        .then(res => res.json())
        .then(data => {

            clearStoreMarkers();

            data.stores.forEach(store => {
                addStoreMarker(store);
            });
        });
}


// ================= FILTER DISTRICT =================
function filterDistrict() {

    let district = document.getElementById("districtSelect").value;

    fetch(`/map/api/district/?district=${district}`)
        .then(res => res.json())
        .then(data => {

            clearStoreMarkers();
            clearBuffer();
            clearRoute();

            data.stores.forEach(store => {
                addStoreMarker(store);
            });
        });
}


// ================= ROUTE =================
async function drawRoute(storeLat, storeLng) {

    if (!userMarker) {
        alert("Vui lòng bấm My Location trước!");
        return;
    }

    const startLat = userMarker.getLatLng().lat;
    const startLng = userMarker.getLatLng().lng;

    try {

        const response = await fetch(
            `/map/api/route/?start_lat=${startLat}&start_lng=${startLng}&end_lat=${storeLat}&end_lng=${storeLng}`
        );

        const data = await response.json();

        if (!response.ok) {
            alert("Không thể lấy đường đi: " + (data.error || "Unknown error"));
            return;
        }

        if (!data.features || data.features.length === 0) {
            alert("Không tìm thấy đường đi!");
            return;
        }

        const coords = data.features[0].geometry.coordinates;
        const routeLatLng = coords.map(c => [c[1], c[0]]);

        clearRoute();

        routeLayer = L.polyline(routeLatLng, {
            weight: 5
        }).addTo(map);

        map.fitBounds(routeLayer.getBounds());

    } catch (error) {
        console.error(error);
        alert("Lỗi khi vẽ đường đi");
    }
}
