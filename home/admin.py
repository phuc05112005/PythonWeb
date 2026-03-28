from django.contrib import admin
from .models import *

class CHITIETGIOHANGAdmin(admin.ModelAdmin):
    list_display = ('sanpham', 'size', 'soluong')

class CHITIETDONHANGAdmin(admin.ModelAdmin):
    list_display = ('sanpham', 'size', 'soluong', 'dongia')

admin.site.register(LOAI)
admin.site.register(SANPHAM)
admin.site.register(GIOHANG)
admin.site.register(DONHANG)
admin.site.register(CUAHANG)

admin.site.register(CHITIETGIOHANG, CHITIETGIOHANGAdmin)
admin.site.register(CHITIETDONHANG, CHITIETDONHANGAdmin)