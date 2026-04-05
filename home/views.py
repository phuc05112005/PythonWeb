from django.shortcuts import get_object_or_404, render
from .models import SANPHAM, LOAI, GIOHANG, CHITIETGIOHANG, DONHANG, CHITIETDONHANG, CUAHANG, TAIKHOAN, HINHANH
from django.shortcuts import redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from django.db.models.functions import TruncMonth
from functools import wraps
from django.contrib import messages

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('dangnhap')
            
        # Tá»± Ä‘á»™ng Ä‘á»“ng bá»™ náº¿u chÆ°a cĂ³ báº£n ghi TAIKHOAN
        if not hasattr(request.user, 'taikhoan'):
            TAIKHOAN.objects.get_or_create(
                user=request.user,
                defaults={'role': 'admin' if request.user.is_staff else 'user'}
            )
            
        # Cho phĂ©p Admin vĂ  Quáº£n lĂ½ truy cáº­p cĂ¡c trang quáº£n trá»‹ chung
        if request.user.taikhoan.role not in ['admin', 'quanly']:
            messages.error(request, "Báº¡n khĂ´ng cĂ³ quyá»n truy cáº­p trang nĂ y!")
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
import calendar
from django.utils.http import url_has_allowed_host_and_scheme

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
    cuahang = CUAHANG.objects.all()
    context = {
        'sanpham': sanpham,
        'cuahang': cuahang,
    }
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
            messages.success(request, "ÄÄƒng kĂ½ thĂ nh cĂ´ng!")
            return redirect('dangnhap')
        else:
            messages.error(request, "ThĂ´ng tin khĂ´ng há»£p lá»‡!")

    else:
        form = UserCreationForm()

    return render(request, 'dangky.html', {'form': form})

def dangnhap(request):
    if request.user.is_authenticated:
        # Äá»“ng bá»™ nhanh náº¿u chÆ°a cĂ³ TAIKHOAN
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
            # Äá»“ng bá»™ nhanh náº¿u chÆ°a cĂ³ TAIKHOAN
            if not hasattr(user, 'taikhoan'):
                TAIKHOAN.objects.get_or_create(user=user, defaults={'role': 'admin' if user.is_staff else 'user'})
                
            if user.taikhoan.role == 'admin':
                return redirect('quantri')
            else:
                return redirect('home')
        else:
            messages.error(request, "TĂªn Ä‘Äƒng nháº­p hoáº·c máº­t kháº©u khĂ´ng chĂ­nh xĂ¡c!")
    return render(request, "dangnhap.html")

def themgiohang(request, sanpham_id):
    if not request.user.is_authenticated:
        return redirect('dangnhap')

    sanpham = SANPHAM.objects.get(id=sanpham_id)
    soluongmua = int(request.POST.get('soluong'))

    size = request.POST.get('size')
    if not size:
        size = 'M'   # đŸ‘ˆ FIX Cá»¨U CHĂY

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

    next_url = request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure()
    ):
        return redirect(next_url)

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
    if not request.user.is_authenticated:
        return redirect('dangnhap')

    gio_hang = GIOHANG.objects.get(khachhang = request.user)
    size = request.GET.get('size')

    chitiet_query = CHITIETGIOHANG.objects.filter(giohang=gio_hang, sanpham_id=sanpham_id)
    if size:
        chitiet_query = chitiet_query.filter(size=size)

    chitiet = chitiet_query.first()
    if chitiet:
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
            messages.error(request, "Äá»‹a chá»‰ khĂ´ng há»£p lá»‡")
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

def donhangcuatoi(request):
    if not request.user.is_authenticated:
        return redirect('dangnhap')

    donhang = DONHANG.objects.filter(khachhang=request.user).order_by('-ngaydat')
    return render(request, 'donhangcuatoi.html', {'donhang': donhang})

def chitietdonhang_khach(request, donhang_id):
    if not request.user.is_authenticated:
        return redirect('dangnhap')

    don_hang = get_object_or_404(DONHANG, id=donhang_id, khachhang=request.user)
    chitiet = CHITIETDONHANG.objects.filter(donhang=don_hang).select_related('sanpham')
    tong_san_pham = sum(item.dongia * item.soluong for item in chitiet)
    phi_giao_hang = max(don_hang.tongtien - tong_san_pham, 0)

    context = {
        'donhang': don_hang,
        'chitiet': chitiet,
        'tong_san_pham': tong_san_pham,
        'phi_giao_hang': phi_giao_hang,
    }
    return render(request, 'chitietdonhang_khach.html', context)

@admin_required
def quantri(request):
    tongsp = SANPHAM.objects.count()
    tongdh1 = DONHANG.objects.filter(trangthai=1).count()
    tongdh2 = DONHANG.objects.filter(trangthai=2).count()
    tongch = CUAHANG.objects.count()

    # Láº¥y thĂ¡ng + nÄƒm hiá»‡n táº¡i
    now = datetime.now()

    donhang = DONHANG.objects.filter(
        trangthai=2,
        ngaydat__month=now.month,
        ngaydat__year=now.year
    )

    tong = 0
    for dh in donhang:
        tong += dh.tongtien

    monthly_revenue = (
        DONHANG.objects.filter(trangthai=2)
        .annotate(month=TruncMonth('ngaydat'))
        .values('month')
        .annotate(total=Sum('tongtien'))
        .order_by('-month')
    )

    selected_month = request.GET.get('month')
    selected_month_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if selected_month:
        try:
            selected_month_date = datetime.strptime(selected_month, '%Y-%m')
        except ValueError:
            selected_month_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    max_day = calendar.monthrange(selected_month_date.year, selected_month_date.month)[1]
    day_from = request.GET.get('day_from')
    day_to = request.GET.get('day_to')
    day_from_value = ''
    day_to_value = ''

    try:
        if day_from is not None and day_from != '':
            day_from_value = max(1, min(int(day_from), max_day))
    except ValueError:
        day_from_value = ''

    try:
        if day_to is not None and day_to != '':
            day_to_value = max(1, min(int(day_to), max_day))
    except ValueError:
        day_to_value = ''

    monthly_details = DONHANG.objects.filter(
        trangthai=2,
        ngaydat__year=selected_month_date.year,
        ngaydat__month=selected_month_date.month
    ).order_by('-ngaydat')

    if day_from_value != '':
        monthly_details = monthly_details.filter(ngaydat__day__gte=day_from_value)
    if day_to_value != '':
        monthly_details = monthly_details.filter(ngaydat__day__lte=day_to_value)

    if day_from_value != '' and day_to_value != '' and day_from_value > day_to_value:
        day_from_value, day_to_value = day_to_value, day_from_value
        monthly_details = DONHANG.objects.filter(
            trangthai=2,
            ngaydat__year=selected_month_date.year,
            ngaydat__month=selected_month_date.month,
            ngaydat__day__gte=day_from_value,
            ngaydat__day__lte=day_to_value
        ).order_by('-ngaydat')

    selected_month_total = monthly_details.aggregate(total=Sum('tongtien'))['total'] or 0

    context = {
        'tongsp': tongsp,
        'tongdh1': tongdh1,
        'tongdh2': tongdh2,
        'tongcuahang': tongch,
        'tongtien': tong,
        'now': now,
        'monthly_revenue': monthly_revenue,
        'selected_month_date': selected_month_date,
        'monthly_details': monthly_details,
        'selected_month_total': selected_month_total,
        'day_from_value': day_from_value,
        'day_to_value': day_to_value,
        'max_day': max_day,
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
        sp.mota = request.POST.get('mota', '')
        loai_id = request.POST.get('loai')
        if loai_id:
            sp.loaisp_id = loai_id
        sp.gia = request.POST.get('gia')
        hinhmoi = request.FILES.get('hinh')
        if hinhmoi:
            sp.hinh = hinhmoi
        sp.soluong = request.POST.get('soluong')
        anhxoa = request.POST.getlist('anhxoa')
        if anhxoa:
            HINHANH.objects.filter(id__in = anhxoa).delete()
        hinhchitietmoi = request.FILES.getlist('hinhchitietmoi')
        for file in hinhchitietmoi:
            HINHANH.objects.create(sanpham = sp, hinh = file)
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
        motasp = request.POST.get('mota', '')
        loai = request.POST.get('loai')
        giasp = request.POST.get('gia')
        soluongsp = request.POST.get('soluong')
        hinhsp = request.FILES.get('hinh')
        hinhchitietsp = request.FILES.getlist('hinhchitiet')
        sp = SANPHAM.objects.create(
            ten = tensp,
            mota = motasp,
            loaisp_id = loai,
            gia = giasp,
            soluong = soluongsp,
            hinh = hinhsp,
        )
        for file in hinhchitietsp:
            HINHANH.objects.create(sanpham = sp, hinh= file)
        sp.save()
        messages.success(request, "luu thanh cong")
        return redirect('quanlysanpham')
    context = {'loai': loaisp}
    return render(request, 'admin/sanpham/themsanpham.html', context)

@admin_required
def quanlydonhang(request):
    donhang = DONHANG.objects.all()

    # ===== FILTER =====
    keyword = request.GET.get('keyword')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    status = request.GET.get('status')   # âœ… thĂªm dĂ²ng nĂ y

    if keyword:
        donhang = donhang.filter(
            Q(ten__icontains=keyword) |
            Q(sdt__icontains=keyword)
        )

    if from_date:
        donhang = donhang.filter(ngaydat__date__gte=from_date)

    if to_date:
        donhang = donhang.filter(ngaydat__date__lte=to_date)

    if min_price:
        donhang = donhang.filter(tongtien__gte=min_price)

    if max_price:
        donhang = donhang.filter(tongtien__lte=max_price)

    # ===== FILTER STATUS (QUAN TRá»ŒNG) =====
    if status == "0":
        donhang = donhang.filter(trangthai=1)  # chÆ°a duyá»‡t
    elif status == "1":
        donhang = donhang.filter(trangthai=2)  # Ä‘Ă£ duyá»‡t

    # ===== PHĂ‚N LOáº I HIá»‚N THá» =====
    donhang1 = donhang.filter(trangthai=1)
    donhang2 = donhang.filter(trangthai=2)

    return render(request, 'admin/donhang/index.html', {
        'donhang1': donhang1,
        'donhang2': donhang2
    })

@admin_required
def duyetdonhang(request, donhang_id):
    if request.method == 'POST':
        dh = DONHANG.objects.get(id = donhang_id)
        dh.trangthai = 2
        dh.save()
        messages.success(request, "Cáº­p nháº­t thĂ nh cĂ´ng")
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
        messages.success(request, "XĂ³a thĂ nh cĂ´ng")
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
        sodienthoai = request.POST.get('sodienthoai', '').strip()
        diachich = request.POST.get('diachi')
        latch = request.POST.get('lat')
        lonch = request.POST.get('lon')
        if not latch or not lonch:
            messages.error(request, "Äá»‹a chá»‰ khĂ´ng há»£p lá»‡")
            context = {'tench': tench, 'sodienthoai': sodienthoai, 'diachich': diachich}
            return render(request, 'admin/cuahang/themcuahang.html', context)
        cuahang = CUAHANG.objects.create(
            ten = tench,
            sodienthoai = sodienthoai,
            diachi = diachich,
            lat = latch,
            lon = lonch,
            hinh = request.FILES.get('hinh'),
            gio_mo = request.POST.get('gio_mo') or "08:00",
            gio_dong = request.POST.get('gio_dong') or "22:00"
        )
        cuahang.save()
        messages.success(request, "ThĂªm thĂ nh cĂ´ng")
        return redirect('quanlycuahang')    
    return render(request, 'admin/cuahang/themcuahang.html')

@admin_required
def suacuahang(request, cuahang_id):
    cuahang = CUAHANG.objects.get(id=cuahang_id)
    if request.method == 'POST':
        cuahang.ten = request.POST.get('ten')
        cuahang.sodienthoai = request.POST.get('sodienthoai', '').strip()
        cuahang.diachi = request.POST.get('diachi')
        
        # Convert lat/lon sang float, Ä‘á»•i ',' thĂ nh '.'
        lat_str = request.POST.get('lat', cuahang.lat)
        lon_str = request.POST.get('lon', cuahang.lon)
        try:
            cuahang.lat = float(str(lat_str).replace(',', '.'))
            cuahang.lon = float(str(lon_str).replace(',', '.'))
        except ValueError:
            cuahang.lat = cuahang.lat
            cuahang.lon = cuahang.lon
        
        # Upload hĂ¬nh má»›i náº¿u cĂ³, giá»¯ nguyĂªn hĂ¬nh cÅ© náº¿u khĂ´ng
        hinhmoi = request.FILES.get('hinh')
        if hinhmoi:
            cuahang.hinh = hinhmoi

        cuahang.gio_mo = request.POST.get('gio_mo') or cuahang.gio_mo
        cuahang.gio_dong = request.POST.get('gio_dong') or cuahang.gio_dong

        cuahang.save()
        messages.success(request, "Cáº­p nháº­t cá»­a hĂ ng thĂ nh cĂ´ng")
        return redirect('quanlycuahang')
    
    context = {'cuahang': cuahang}
    return render(request, 'admin/cuahang/suacuahang.html', context)

@admin_required
def xoacuahang(request, cuahang_id):
    cuahang = CUAHANG.objects.get(id = cuahang_id)
    if request.method == 'POST':
        cuahang.delete()
        messages.success(request, "XĂ³a thĂ nh cĂ´ng")
    return redirect('quanlycuahang')
def map_view(request):

    cuahang = CUAHANG.objects.all()
    data = []

    now = datetime.now().time()

    for ch in cuahang:

        is_open = ch.gio_mo <= now <= ch.gio_dong

        data.append({
            "ten": ch.ten,
            "sodienthoai": ch.sodienthoai,
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
    # Chá»‰ Admin má»›i Ä‘Æ°á»£c vĂ o trang quáº£n lĂ½ tĂ i khoáº£n
    if request.user.taikhoan.role != 'admin':
        messages.error(request, "Chá»‰ Admin má»›i cĂ³ quyá»n quáº£n lĂ½ tĂ i khoáº£n!")
        return redirect('quantri')

    # Tá»± Ä‘á»™ng táº¡o TAIKHOAN cho cĂ¡c user cÅ© chÆ°a cĂ³
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
    # Chá»‰ Admin má»›i cĂ³ quyá»n cáº­p nháº­t ngÆ°á»i khĂ¡c
    if request.user.taikhoan.role != 'admin':
        messages.error(request, "Chá»‰ Admin má»›i cĂ³ quyá»n thay Ä‘á»•i phĂ¢n quyá»n!")
        return redirect('quantri')

    if request.method == 'POST':
        try:
            tk = TAIKHOAN.objects.select_related('user').get(user__id=user_id)
            # KhĂ´ng cho phĂ©p thay Ä‘á»•i superuser hoáº·c chĂ­nh mĂ¬nh
            if tk.user.is_superuser:
                messages.error(request, "KhĂ´ng thá»ƒ thay Ä‘á»•i quyá»n cá»§a Super Admin!")
                return redirect('quanlytaikhoan')
            if tk.user.id == request.user.id:
                messages.error(request, "KhĂ´ng thá»ƒ thay Ä‘á»•i quyá»n cá»§a chĂ­nh báº¡n!")
                return redirect('quanlytaikhoan')

            quyen_moi = request.POST.get('quyen')
            if quyen_moi in ['admin', 'quanly', 'user']:
                tk.role = quyen_moi
                
                # Äá»“ng bá»™ is_staff (Admin vĂ  Quáº£n lĂ½ Ä‘á»u cáº§n is_staff=True Ä‘á»ƒ vĂ o trang quáº£n trá»‹)
                if quyen_moi in ['admin', 'quanly']:
                    tk.user.is_staff = True
                else:
                    tk.user.is_staff = False
                
                tk.user.save()
                tk.save()
                messages.success(request, f'ÄĂ£ cáº­p nháº­t quyá»n cho {tk.user.username} thĂ nh {tk.get_role_display()}!')
        except TAIKHOAN.DoesNotExist:
            messages.error(request, "TĂ i khoáº£n khĂ´ng tá»“n táº¡i!")
    return redirect('quanlytaikhoan')

def xoataikhoan(request, id):
    if request.method == "POST":
        user = get_object_or_404(User, id=id)

        # âŒ KhĂ´ng cho xĂ³a chĂ­nh mĂ¬nh
        if user == request.user:
            messages.error(request, "KhĂ´ng thá»ƒ xĂ³a tĂ i khoáº£n cá»§a chĂ­nh báº¡n!")
            return redirect('quanlytaikhoan')

        # âŒ KhĂ´ng cho xĂ³a super admin
        if user.is_superuser:
            messages.error(request, "KhĂ´ng thá»ƒ xĂ³a Super Admin!")
            return redirect('quanlytaikhoan')

        user.delete()
        messages.success(request, "XĂ³a tĂ i khoáº£n thĂ nh cĂ´ng!")

    return redirect('quanlytaikhoan')

from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages
from .forms import MailForm  # táº¡o form cho email

from django.conf import settings

def send_mailtrap(request):
    if request.method == 'POST':
        form = MailForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']

            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    ['phuc052005@gmail.com'],
                    fail_silently=False
                )
                messages.success(request, 'Email Ä‘Ă£ gá»­i thĂ nh cĂ´ng!')
            except Exception as e:
                messages.error(request, f'Gá»­i email tháº¥t báº¡i: {e}')

            return redirect('send_mailtrap')
    else:
        form = MailForm()

    return render(request, 'send_mailtrap.html', {'form': form})

def gioithieu(request):
    return render(request, 'gioithieu.html')

def chinhsachbaohanh(request):
    return render(request, 'chinhsachbaohanh.html')

def chinhsachdoitra(request):
    return render(request, 'chinhsachdoitra.html')

def dieukhoansudung(request):
    return render(request, 'dieukhoansudung.html')


