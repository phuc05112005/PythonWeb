from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

SIZE_CHOICES = [
    ('S', 'S'),
    ('M', 'M'),
    ('L', 'L'),
    ('XL', 'XL'),
]


class LOAI(models.Model):
    loai = models.CharField(max_length=100)

    def __str__(self):
        return self.loai


class SANPHAM(models.Model):
    loaisp = models.ForeignKey(LOAI, on_delete=models.CASCADE)
    ten = models.CharField(max_length=200)
    mota = models.TextField(blank=True, default='')
    gia = models.IntegerField()
    hinh = models.ImageField(null=True, blank=True)
    soluong = models.IntegerField(default=0) # Tổng tồn kho toàn hệ thống

    def __str__(self):
        return self.ten

    @property
    def hinhurl(self):
        try:
            return self.hinh.url
        except Exception:
            return ''

    @property
    def ton_theo_size(self):
        # Trả về tồn kho tổng theo size (tất cả cửa hàng)
        res = {}
        for s, _ in SIZE_CHOICES:
            res[s] = self.tonkho_sizes.filter(size=s).aggregate(models.Sum('soluong'))['soluong__sum'] or 0
        return res


class CUAHANG(models.Model):
    ten = models.CharField(max_length=100)
    sodienthoai = models.CharField(max_length=15, blank=True, default='')
    diachi = models.CharField(max_length=100)
    lat = models.FloatField()
    lon = models.FloatField()
    hinh = models.ImageField(upload_to='cuahang/', null=True, blank=True)
    gio_mo = models.TimeField(default='08:00')
    gio_dong = models.TimeField(default='22:00')

    def __str__(self):
        return self.ten

    @property
    def hinhurl(self):
        try:
            return self.hinh.url
        except Exception:
            return ''


class TONKHOSIZE(models.Model):
    sanpham = models.ForeignKey(SANPHAM, on_delete=models.CASCADE, related_name='tonkho_sizes')
    cuahang = models.ForeignKey(CUAHANG, on_delete=models.CASCADE, related_name='tonkho_sanpham', null=True) # null=True cho migration
    size = models.CharField(max_length=2, choices=SIZE_CHOICES)
    soluong = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['sanpham', 'size', 'cuahang'], name='uniq_tonkho_sanpham_size_cuahang'),
            models.CheckConstraint(condition=models.Q(soluong__gte=0), name='tonkho_size_non_negative'),
        ]

    def __str__(self):
        return f"{self.sanpham.ten} - {self.cuahang.ten if self.cuahang else 'N/A'} - {self.size}: {self.soluong}"


class GIOHANG(models.Model):
    khachhang = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.khachhang.username


class CHITIETGIOHANG(models.Model):
    giohang = models.ForeignKey(GIOHANG, on_delete=models.CASCADE)
    sanpham = models.ForeignKey(SANPHAM, on_delete=models.CASCADE)
    size = models.CharField(max_length=2, choices=SIZE_CHOICES, default='M')
    soluong = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.sanpham.ten} - {self.size} x {self.soluong}"


class DONHANG(models.Model):
    khachhang = models.ForeignKey(User, on_delete=models.CASCADE)
    cuahang = models.ForeignKey(CUAHANG, on_delete=models.SET_NULL, null=True, blank=True) # Cửa hàng xử lý đơn
    ten = models.CharField(max_length=100)
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
    size = models.CharField(max_length=2, choices=SIZE_CHOICES, default='M')
    soluong = models.IntegerField()
    dongia = models.IntegerField()


class LICHSUKHO(models.Model):
    LOAI_BIENDONG_CHOICES = [
        ('nhap', 'Nhap kho'),
        ('xuat', 'Xuat kho'),
        ('dieuchinh_tang', 'Dieu chinh tang'),
        ('dieuchinh_giam', 'Dieu chinh giam'),
    ]

    sanpham = models.ForeignKey(SANPHAM, on_delete=models.CASCADE, related_name='lichsu_kho')
    cuahang = models.ForeignKey(CUAHANG, on_delete=models.CASCADE, null=True, blank=True)
    size = models.CharField(max_length=2, choices=SIZE_CHOICES)
    loai_biendong = models.CharField(max_length=20, choices=LOAI_BIENDONG_CHOICES)
    soluong_thaydoi = models.IntegerField()
    ton_truoc = models.IntegerField(default=0)
    ton_sau = models.IntegerField(default=0)
    ghichu = models.CharField(max_length=255, blank=True, default='')
    nguoithuchien = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    thoigian = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-thoigian', '-id']

    def __str__(self):
        return f"{self.sanpham.ten} - {self.size} tại {self.cuahang.ten if self.cuahang else 'N/A'}"


class TAIKHOAN(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('quanly', 'Quản lý'),
        ('user', 'User'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='taikhoan')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


@receiver(post_save, sender=User)
def tao_taikhoan(sender, instance, created, **kwargs):
    if created:
        role = 'admin' if instance.is_staff else 'user'
        TAIKHOAN.objects.create(user=instance, role=role)


class HINHANH(models.Model):
    sanpham = models.ForeignKey(SANPHAM, on_delete=models.CASCADE, related_name='hinhanh')
    hinh = models.ImageField(null=True, blank=True)
