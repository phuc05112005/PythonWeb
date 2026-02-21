from django.urls import path
from . import views

urlpatterns = [
    path('', views.map_view, name='map'),
    path('api/nearby/', views.nearby_api),
    path('api/district/', views.district_api),
    path('api/route/', views.route_api),
    path('api/all/', views.all_stores_api),

]
