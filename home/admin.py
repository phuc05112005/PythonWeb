from django.contrib import admin
from .models import SANPHAM,LOAI, GIOHANG, CHITIETGIOHANG, DONHANG, CHITIETDONHANG, CUAHANG
# Register your models here.
admin.site.register(SANPHAM)
admin.site.register(LOAI)
admin.site.register(GIOHANG)
admin.site.register(CHITIETGIOHANG)
admin.site.register(DONHANG)
admin.site.register(CHITIETDONHANG)
admin.site.register(CUAHANG)