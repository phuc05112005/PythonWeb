from django.shortcuts import get_object_or_404, render
from .models import SANPHAM, LOAI, GIOHANG, CHITIETGIOHANG, DONHANG, CHITIETDONHANG, CUAHANG, TAIKHOAN
from django.shortcuts import redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from functools import wraps

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('dangnhap')
            
        # Tự động đồng bộ nếu chưa có bản ghi TAIKHOAN
        if not hasattr(request.user, 'taikhoan'):
            TAIKHOAN.objects.get_or_create(
                user=request.user,
                defaults={'role': 'admin' if request.user.is_staff else 'user'}
            )
            
        # Cho phép Admin và Quản lý truy cập các trang quản trị chung
        if request.user.taikhoan.role not in ['admin', 'quanly']:
            messages.error(request, "Bạn không có quyền truy cập trang này!")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.core.paginator import Paginator
from .tool import cuahanggannhat
import os
import json
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime

# Create your views here.
def home(request, loai_id = None):
    loai = LOAI.objects.all()
    if loai_id is None:
        sanpham = SANPHAM.objects.all()
    else: 
        sanpham = SANPHAM.objects.filter(loaisp_id = loai_id)
    page = Paginator(sanpham, 9)
    page_number = request.GET.get('page')
    sanphamphantrang = page.get_page(page_number)
    context = {'sanpham': sanphamphantrang, 'loai': loai, 'loai_id': loai_id}
    return render(request,'home.html', context)

def chitietsp(request, sanpham_id):
    sanpham = get_object_or_404(SANPHAM, id = sanpham_id)
    context = {'sanpham': sanpham}
    return render(request, 'chitietsp.html', context)

def soluong(request):
    count = 0
    if request.user.is_authenticated:
        giohang, created = GIOHANG.objects.get_or_create(khachhang = request.user)
        if giohang:
            chitiet = CHITIETGIOHANG.objects.filter(giohang = giohang)
            for sp in chitiet:
                count += sp.soluong
    return {'count': count}

def dangky(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():  
            form.save()
            messages.success(request, "Đăng ký thành công!")
            return redirect('dangnhap')
        else:
            messages.error(request, "Thông tin không hợp lệ!")

    else:
        form = UserCreationForm()

    return render(request, 'dangky.html', {'form': form})

def dangnhap(request):
    if request.user.is_authenticated:
        # Đồng bộ nhanh nếu chưa có TAIKHOAN
        if not hasattr(request.user, 'taikhoan'):
            TAIKHOAN.objects.get_or_create(user=request.user, defaults={'role': 'admin' if request.user.is_staff else 'user'})
            
        if request.user.taikhoan.role == 'admin':
            return redirect('quantri')
        return redirect('home')
    if request.method == 'POST':
        taikhoan = request.POST.get('username')
        matkhau = request.POST.get('password')
        user = authenticate(request, username = taikhoan, password = matkhau)
        if user is not None:
            login(request, user)
            # Đồng bộ nhanh nếu chưa có TAIKHOAN
            if not hasattr(user, 'taikhoan'):
                TAIKHOAN.objects.get_or_create(user=user, defaults={'role': 'admin' if user.is_staff else 'user'})
                
            if user.taikhoan.role == 'admin':
                return redirect('quantri')
            else:
                return redirect('home')
        else:
            messages.error(request, "Tên đăng nhập hoặc mật khẩu không chính xác!")
    return render(request, "dangnhap.html")

def themgiohang(request, sanpham_id):
    if not request.user.is_authenticated:
        return redirect('dangnhap')

    sanpham = SANPHAM.objects.get(id=sanpham_id)
    soluongmua = int(request.POST.get('soluong'))

    size = request.POST.get('size')
    if not size:
        size = 'M'   # 👈 FIX CỨU CHÁY

    giohang, created = GIOHANG.objects.get_or_create(khachhang=request.user)

    chitiet, created = CHITIETGIOHANG.objects.get_or_create(
        giohang=giohang,
        sanpham=sanpham,
        size=size,
        defaults={'soluong': soluongmua}
    )

    if not created:
        chitiet.soluong += soluongmua
        chitiet.save()

    return redirect('home')

def suagiohang(request, sanpham_id):
    if request.method == 'POST':
        soluongmoi = int(request.POST.get('soluong'))
        gio_hang = GIOHANG.objects.get(khachhang = request.user)
        chitiet = CHITIETGIOHANG.objects.get(giohang = gio_hang, sanpham_id = sanpham_id, size=request.POST.get('size'))
        chitiet.soluong = soluongmoi
        chitiet.save()
    return redirect('giohang')

def xoagiohang(request, sanpham_id):
    gio_hang = GIOHANG.objects.get(khachhang = request.user)
    chitiet = CHITIETGIOHANG.objects.get(giohang = gio_hang, sanpham_id = sanpham_id)
    chitiet.delete()
    return redirect('giohang')

def giohang(request):
    if not request.user.is_authenticated:
        return redirect('dangnhap')
    gio_hang, created = GIOHANG.objects.get_or_create(khachhang = request.user)
    sanpham = CHITIETGIOHANG.objects.filter(giohang = gio_hang)
    tongtien = 0
    for mon in sanpham:
        tongtien += mon.sanpham.gia * mon.soluong
    context = {'sanpham': sanpham, 'tongtien': tongtien}
    return render(request, 'giohang.html', context)
    

def thanhtoan(request):
    if not request.user.is_authenticated:
        return redirect('dangnhap')
    gio_hang, created = GIOHANG.objects.get_or_create(khachhang = request.user)
    san_pham = CHITIETGIOHANG.objects.filter(giohang = gio_hang)
    tienship = 0
    tong = 0
    km = 0
    tongtiendonhang = 0
    for mon in san_pham:
        tongtiendonhang += mon.sanpham.gia * mon.soluong
    if request.method == 'POST':
        tenkh = request.POST.get('ten')
        sdtkh = request.POST.get('sdt')
        diachikh = request.POST.get('diachi')
        latkh = float(request.POST.get('lat'))
        lonkh = float(request.POST.get('lon'))
        action = request.POST.get('action')
        if not latkh or not lonkh:
            messages.error(request, "Địa chỉ không hợp lệ")
            context = {'tenkh': tenkh, 'sdtkh': sdtkh, 'diachikh': diachikh, 'sanpham': san_pham, 'tongtien': tongtiendonhang}
            return render(request, 'thanhtoan.html', context)
        cuahang = CUAHANG.objects.all()
        ch_gan_nhat, km = cuahanggannhat(latkh, lonkh, cuahang)
        tienship = int(km * 3000)
        tong = tongtiendonhang + tienship
        if action == 'thanhtoan':
            don_hang = DONHANG.objects.create(
                khachhang = request.user,
                ten = tenkh,
                sdt = sdtkh,
                diachi = diachikh,
                lat = latkh,
                lon = lonkh,
                tongtien = tong
            )
            for mon in san_pham:
                CHITIETDONHANG.objects.create(
                    donhang = don_hang,
                    sanpham = mon.sanpham,
                    size=mon.size,
                    soluong = mon.soluong,
                    dongia = mon.sanpham.gia
                )
                sp = mon.sanpham
                sp.soluong -= mon.soluong
                sp.save()
            san_pham.delete()
            return render(request, 'camon.html')
    context = {
        'tenkh': request.POST.get('ten'), 
        'sdtkh': request.POST.get('sdt'), 
        'diachikh': request.POST.get('diachi'), 
        'sanpham': san_pham, 
        'tongtiendonhang': tongtiendonhang, 
        'tongtien': tong,
        'km': km,
        'tienship': tienship, 
        'latkh': request.POST.get('lat'),
        'lonkh': request.POST.get('lon')
        }
    return render(request, 'thanhtoan.html', context)

@admin_required
def quantri(request):
    tongsp = SANPHAM.objects.count()
    tongdh1 = DONHANG.objects.filter(trangthai=1).count()
    tongdh2 = DONHANG.objects.filter(trangthai=2).count()
    tongch = CUAHANG.objects.count()

    # Lấy tháng + năm hiện tại
    now = datetime.now()

    donhang = DONHANG.objects.filter(
        trangthai=2,
        ngaydat__month=now.month,
        ngaydat__year=now.year
    )

    tong = 0
    for dh in donhang:
        tong += dh.tongtien

    context = {
        'tongsp': tongsp,
        'tongdh1': tongdh1,
        'tongdh2': tongdh2,
        'tongcuahang': tongch,
        'tongtien': tong,
        'now': now
    }
    return render(request, 'quantri.html', context)

@admin_required
def quanlysanpham(request):
    sp = SANPHAM.objects.all().order_by('id')
    loai = LOAI.objects.all()

    # ===== FILTER =====
    keyword = request.GET.get('keyword')
    loai_id = request.GET.get('loai')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    tonkho = request.GET.get('tonkho')

    if keyword:
        sp = sp.filter(ten__icontains=keyword)

    if loai_id:
        sp = sp.filter(loaisp_id=loai_id)

    if min_price:
        sp = sp.filter(gia__gte=min_price)

    if max_price:
        sp = sp.filter(gia__lte=max_price)

    if tonkho == "con":
        sp = sp.filter(soluong__gt=0)
    elif tonkho == "het":
        sp = sp.filter(soluong=0)

    context = {
        'sanpham': sp,
        'loai': loai,
    }

    return render(request, 'admin/sanpham/index.html', context)

@admin_required
def xoasanpham(request, sanpham_id):
    if request.method == 'POST':
        sp = SANPHAM.objects.get(id = sanpham_id)
        if sp.hinh:
            if os.path.isfile(sp.hinh.path):
                os.remove(sp.hinh.path)
        sp.delete()
        messages.success(request, "Da xoa thanh cong")
    return redirect('quanlysanpham')

@admin_required
def suasanpham(request, sanpham_id):
    sp = SANPHAM.objects.get(id = sanpham_id)
    loai = LOAI.objects.all()
    if request.method == 'POST':
        sp.ten = request.POST.get('ten')
        loai_id = request.POST.get('loai')
        if loai_id:
            sp.loaisp_id = loai_id
        sp.gia = request.POST.get('gia')
        hinhmoi = request.FILES.get('hinh')
        if hinhmoi:
            sp.hinh = hinhmoi
        sp.soluong = request.POST.get('soluong')
        sp.save()
        messages.success(request, "cap nhat thanh cong")
        return redirect('quanlysanpham')
    context = {'sanpham': sp, 'dsloai': loai}
    return render(request, 'admin/sanpham/suasanpham.html', context)

@admin_required
def themsanpham(request):
    loaisp = LOAI.objects.all()
    if request.method == 'POST':
        tensp = request.POST.get('ten')
        loai = request.POST.get('loai')
        giasp = request.POST.get('gia')
        soluongsp = request.POST.get('soluong')
        hinhsp = request.FILES.get('hinh')
        sp = SANPHAM.objects.create(
            ten = tensp,
            loaisp_id = loai,
            gia = giasp,
            soluong = soluongsp,
            hinh = hinhsp,
        )
        sp.save()
        messages.success(request, "luu thanh cong")
        return redirect('quanlysanpham')
    context = {'loai': loaisp}
    return render(request, 'admin/sanpham/themsanpham.html', context)

@admin_required
def quanlydonhang(request):
    donhang1 = DONHANG.objects.filter(trangthai = 1)
    donhang2 = DONHANG.objects.filter(trangthai = 2)
    context = {'donhang1': donhang1, 'donhang2': donhang2}
    return render(request, 'admin/donhang/index.html', context)

@admin_required
def duyetdonhang(request, donhang_id):
    if request.method == 'POST':
        dh = DONHANG.objects.get(id = donhang_id)
        dh.trangthai = 2
        dh.save()
        messages.success(request, "Cập nhật thành công")
    return redirect('quanlydonhang')
    
@admin_required
def chitietdonhang(request, donhang_id):
    don_hang = DONHANG.objects.get(id = donhang_id)
    chitiet = CHITIETDONHANG.objects.filter(donhang = don_hang)
    context = {'chitiet': chitiet}
    return render(request, 'admin/donhang/chitietdonhang.html', context)

@admin_required
def xoadonhang(request, donhang_id):
    if request.method == 'POST':
        donhang = DONHANG.objects.get(id = donhang_id)
        donhang.delete()
        messages.success(request, "Xóa thành công")
    return redirect('quanlydonhang')

@admin_required
def quanlyloai(request):
    loai = LOAI.objects.all()
    context = {'loai': loai}
    return render(request, 'admin/loaisp/index.html', context)

@admin_required
def themloai(request):
    if request.method == 'POST':
        loaisp = request.POST.get('loai')
        loai_sp = LOAI.objects.create(
            loai = loaisp
        )
        loai_sp.save()
        messages.success(request, "them thanh cong")
        return redirect('quanlyloai')
    return render(request, 'admin/loaisp/themloai.html')

@admin_required
def xoaloai(request, loai_id):
    if request.method == 'POST':
        loaisp = LOAI.objects.get(id = loai_id)
        loaisp.delete()
        messages.success(request, "Xoa thanh cong")
    return redirect('quanlyloai')

@admin_required
def sualoai(request, loai_id):
    loaisp = LOAI.objects.get(id = loai_id)
    if request.method == 'POST':
        loaisp.loai = request.POST.get('loai')
        loaisp.save()
        messages.success(request, "cap nhat thanh cong")
        return redirect('quanlyloai')
    context = {'loai': loaisp}
    return render(request, 'admin/loaisp/sualoai.html', context)

def timkiem(request):
    loai = LOAI.objects.all()
    if request.method == 'POST':
        search = request.POST.get('search')
        kq = SANPHAM.objects.filter(ten__unaccent__icontains = search)
    page = Paginator(kq, 9)
    page_number = request.GET.get('page')
    sanphamphantrang = page.get_page(page_number)
    context = {'kq': sanphamphantrang, 'search':search, 'loai': loai}
    return render(request, 'search.html', context)

@admin_required
def quanlycuahang(request):
    cuahang = CUAHANG.objects.all()
    context = {'cuahang': cuahang}
    return render(request, 'admin/cuahang/index.html', context)

@admin_required
def themcuahang(request):
    if request.method == 'POST':
        tench = request.POST.get('ten')
        diachich = request.POST.get('diachi')
        latch = request.POST.get('lat')
        lonch = request.POST.get('lon')
        if not latch or not lonch:
            messages.error(request, "Địa chỉ không hợp lệ")
            context = {'tench': tench, 'diachich': diachich}
            return render(request, 'admin/cuahang/themcuahang.html', context)
        cuahang = CUAHANG.objects.create(
            ten = tench,
            diachi = diachich,
            lat = latch,
            lon = lonch,
            hinh = request.FILES.get('hinh'),
            rating = request.POST.get('rating') or 4.5,
            gio_mo = request.POST.get('gio_mo') or "08:00",
            gio_dong = request.POST.get('gio_dong') or "22:00"
        )
        cuahang.save()
        messages.success(request, "Thêm thành công")
        return redirect('quanlycuahang')    
    return render(request, 'admin/cuahang/themcuahang.html')

@admin_required
def suacuahang(request, cuahang_id):
    cuahang = CUAHANG.objects.get(id=cuahang_id)
    if request.method == 'POST':
        cuahang.ten = request.POST.get('ten')
        cuahang.diachi = request.POST.get('diachi')
        
        # Convert lat/lon sang float, đổi ',' thành '.'
        lat_str = request.POST.get('lat', cuahang.lat)
        lon_str = request.POST.get('lon', cuahang.lon)
        try:
            cuahang.lat = float(str(lat_str).replace(',', '.'))
            cuahang.lon = float(str(lon_str).replace(',', '.'))
        except ValueError:
            cuahang.lat = cuahang.lat
            cuahang.lon = cuahang.lon
        
        # Upload hình mới nếu có, giữ nguyên hình cũ nếu không
        hinhmoi = request.FILES.get('hinh')
        if hinhmoi:
            cuahang.hinh = hinhmoi

        cuahang.gio_mo = request.POST.get('gio_mo') or cuahang.gio_mo
        cuahang.gio_dong = request.POST.get('gio_dong') or cuahang.gio_dong

        cuahang.save()
        messages.success(request, "Cập nhật cửa hàng thành công")
        return redirect('quanlycuahang')
    
    context = {'cuahang': cuahang}
    return render(request, 'admin/cuahang/suacuahang.html', context)

@admin_required
def xoacuahang(request, cuahang_id):
    cuahang = CUAHANG.objects.get(id = cuahang_id)
    if request.method == 'POST':
        cuahang.delete()
        messages.success(request, "Xóa thành công")
    return redirect('quanlycuahang')
def map_view(request):

    cuahang = CUAHANG.objects.all()
    data = []

    now = datetime.now().time()

    for ch in cuahang:

        is_open = ch.gio_mo <= now <= ch.gio_dong

        data.append({
            "ten": ch.ten,
            "lat": ch.lat,
            "lon": ch.lon,
            "diachi": ch.diachi,
            "hinh": ch.hinh.url if ch.hinh else "/static/images/cuahang1.jpg",
            "gio_mo": ch.gio_mo.strftime("%H:%M"),
            "gio_dong": ch.gio_dong.strftime("%H:%M"),
            "is_open": is_open
        })
    return render(request, "map.html", {
        "stores_json": json.dumps(data, cls=DjangoJSONEncoder)
    })

@admin_required
def quanlytaikhoan(request):
    # Chỉ Admin mới được vào trang quản lý tài khoản
    if request.user.taikhoan.role != 'admin':
        messages.error(request, "Chỉ Admin mới có quyền quản lý tài khoản!")
        return redirect('quantri')

    # Tự động tạo TAIKHOAN cho các user cũ chưa có
    for u in User.objects.all():
        TAIKHOAN.objects.get_or_create(
            user=u,
            defaults={'role': 'admin' if u.is_staff else 'user'}
        )

    taikhoan = TAIKHOAN.objects.select_related('user').all().order_by('user__id')

    # Filter
    keyword = request.GET.get('keyword')
    role = request.GET.get('role')

    if keyword:
        taikhoan = taikhoan.filter(user__username__icontains=keyword)

    if role:
        taikhoan = taikhoan.filter(role=role)

    tong_taikhoan = TAIKHOAN.objects.count()
    tong_admin = TAIKHOAN.objects.filter(role='admin').count()
    tong_quanly = TAIKHOAN.objects.filter(role='quanly').count()
    tong_user = TAIKHOAN.objects.filter(role='user').count()

    context = {
        'taikhoan': taikhoan,
        'tong_taikhoan': tong_taikhoan,
        'tong_admin': tong_admin,
        'tong_quanly': tong_quanly,
        'tong_user': tong_user,
    }
    return render(request, 'admin/taikhoan/index.html', context)

@admin_required
def capnhatquyen(request, user_id):
    # Chỉ Admin mới có quyền cập nhật người khác
    if request.user.taikhoan.role != 'admin':
        messages.error(request, "Chỉ Admin mới có quyền thay đổi phân quyền!")
        return redirect('quantri')

    if request.method == 'POST':
        try:
            tk = TAIKHOAN.objects.select_related('user').get(user__id=user_id)
            # Không cho phép thay đổi superuser hoặc chính mình
            if tk.user.is_superuser:
                messages.error(request, "Không thể thay đổi quyền của Super Admin!")
                return redirect('quanlytaikhoan')
            if tk.user.id == request.user.id:
                messages.error(request, "Không thể thay đổi quyền của chính bạn!")
                return redirect('quanlytaikhoan')

            quyen_moi = request.POST.get('quyen')
            if quyen_moi in ['admin', 'quanly', 'user']:
                tk.role = quyen_moi
                
                # Đồng bộ is_staff (Admin và Quản lý đều cần is_staff=True để vào trang quản trị)
                if quyen_moi in ['admin', 'quanly']:
                    tk.user.is_staff = True
                else:
                    tk.user.is_staff = False
                
                tk.user.save()
                tk.save()
                messages.success(request, f'Đã cập nhật quyền cho {tk.user.username} thành {tk.get_role_display()}!')
        except TAIKHOAN.DoesNotExist:
            messages.error(request, "Tài khoản không tồn tại!")
    return redirect('quanlytaikhoan')