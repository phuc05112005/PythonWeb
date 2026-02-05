from django.db import models

# Create your models here.
class LOAI(models.Model):
    loai = models.CharField(max_length=100)

    def __str__(self):
        return self.loai


class SANPHAM(models.Model):
    loaisp = models.ForeignKey(LOAI, on_delete=models.CASCADE)
    ten = models.CharField(max_length=200)
    gia = models.IntegerField()
    mota = models.TextField()
    hinh = models.ImageField(upload_to="hinh/")
    soluong = models.IntegerField(default=0)

    def __str__(self):
        return self.ten