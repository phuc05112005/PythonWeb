from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class LOAI(models.Model):
    loai = models.CharField(max_length=100)

    def __str__(self):
        return self.loai


class SANPHAM(models.Model):
    loaisp = models.ForeignKey(LOAI, on_delete=models.CASCADE)
    ten = models.CharField(max_length=200)
    gia = models.IntegerField()
    hinh = models.ImageField(null=True, blank=True)
    soluong = models.IntegerField(default=0)

    def __str__(self):
        return self.ten
    @property
    def hinhurl(self):
        try:
            url = self.hinh.url
        except:
            url = ''
        return url
    
class GIOHANG(models.Model):
    khachhang = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.khachhang.username

class CHITIETGIOHANG(models.Model):
    SIZE_CHOICES = [
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
    ]

    giohang = models.ForeignKey(GIOHANG, on_delete=models.CASCADE)
    sanpham = models.ForeignKey(SANPHAM, on_delete=models.CASCADE)
    size = models.CharField(max_length=2, choices=SIZE_CHOICES, default='M')  # 👈 THÊM
    soluong = models.IntegerField(default=1) 

    def __str__(self):
        return f"{self.sanpham.ten} - {self.size} x {self.soluong}"
    
class DONHANG(models.Model):
    khachhang = models.ForeignKey(User , on_delete=models.CASCADE)
    ten = models.CharField(max_length = 100)
    sdt = models.CharField(max_length=11)
    diachi = models.TextField()
    tongtien = models.IntegerField()
    ngaydat = models.DateTimeField(auto_now_add=True)
    trangthai = models.IntegerField(default=1)
    lat = models.FloatField()
    lon = models.FloatField()

    def __str__(self):
        return f"Don hang {self.id} cua {self.ten}"
    
class CHITIETDONHANG(models.Model):
    donhang = models.ForeignKey(DONHANG, on_delete=models.CASCADE)
    sanpham = models.ForeignKey(SANPHAM, on_delete=models.CASCADE)
    size = models.CharField(max_length=2, default='M')  # 👈 THÊM
    soluong = models.IntegerField()
    dongia = models.IntegerField()

class CUAHANG(models.Model):
    ten = models.CharField(max_length=100)
    diachi = models.CharField(max_length=100)
    lat = models.FloatField()
    lon = models.FloatField()
    hinh = models.ImageField(upload_to='cuahang/', null=True, blank=True)

    gio_mo = models.TimeField(default="08:00")
    gio_dong = models.TimeField(default="22:00")

    def __str__(self):
        return self.ten

    @property
    def hinhurl(self):
        try:
            return self.hinh.url
        except:
            return ''
    