from django.shortcuts import get_object_or_404, render
from .models import SANPHAM, LOAI, GIOHANG, CHITIETGIOHANG, DONHANG, CHITIETDONHANG, CUAHANG
from django.shortcuts import redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.core.paginator import Paginator
from .tool import cuahanggannhat
import os
import json
from django.core.serializers.json import DjangoJSONEncoder

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
    form = UserCreationForm()
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        form.save()
        return redirect('dangnhap')
    context = {'form': form}
    return render(request, 'dangky.html', context)

def dangnhap(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('quantri')
        return redirect('home')
    if request.method == 'POST':
        taikhoan = request.POST.get('username')
        matkhau = request.POST.get('password')
        user = authenticate(request, username = taikhoan, password = matkhau)
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('quantri')
            else:
                return redirect('home')
        else:
            messages.error(request, "Tên đăng nhập hoặc mật khẩu không chính xác!")
    return render(request, "dangnhap.html")

def themgiohang(request, sanpham_id):
    if not request.user.is_authenticated:
        return redirect('dangnhap')
    sanpham = SANPHAM.objects.get(id = sanpham_id)
    soluongmua = int(request.POST.get('soluong'))
    giohang, created = GIOHANG.objects.get_or_create(khachhang = request.user)
    chitiet, created = CHITIETGIOHANG.objects.get_or_create(giohang = giohang, sanpham = sanpham, defaults={'soluong': soluongmua})
    if not created:
        chitiet.soluong += soluongmua
        chitiet.save()
    return redirect('home')

def suagiohang(request, sanpham_id):
    if request.method == 'POST':
        soluongmoi = int(request.POST.get('soluong'))
        gio_hang = GIOHANG.objects.get(khachhang = request.user)
        chitiet = CHITIETGIOHANG.objects.get(giohang = gio_hang, sanpham_id = sanpham_id)
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

@staff_member_required(login_url='dangnhap')
def quantri(request):
    tongsp = SANPHAM.objects.count()
    tongdh1 = DONHANG.objects.filter(trangthai = 1).count()
    tongdh2 = DONHANG.objects.filter(trangthai = 2).count()
    tongch = CUAHANG.objects.count()
    tong = 0
    donhang = DONHANG.objects.filter(trangthai = 2)
    for dh in donhang:
        tong += dh.tongtien
    context = {'tongsp': tongsp, 'tongdh1': tongdh1, 'tongdh2': tongdh2, 'tongcuahang': tongch, 'tongtien': tong}
    return render(request, 'quantri.html', context)

@staff_member_required(login_url='dangnhap')
def quanlysanpham(request):
    sp = SANPHAM.objects.all().order_by('id')
    context = {'sanpham': sp}
    return render(request, 'admin/sanpham/index.html', context)

@staff_member_required(login_url='dangnhap')
def xoasanpham(request, sanpham_id):
    if request.method == 'POST':
        sp = SANPHAM.objects.get(id = sanpham_id)
        if sp.hinh:
            if os.path.isfile(sp.hinh.path):
                os.remove(sp.hinh.path)
        sp.delete()
        messages.success(request, "Da xoa thanh cong")
    return redirect('quanlysanpham')

@staff_member_required(login_url='dangnhap')
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

@staff_member_required(login_url='dangnhap')
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

@staff_member_required(login_url='dangnhap')
def quanlydonhang(request):
    donhang1 = DONHANG.objects.filter(trangthai = 1)
    donhang2 = DONHANG.objects.filter(trangthai = 2)
    context = {'donhang1': donhang1, 'donhang2': donhang2}
    return render(request, 'admin/donhang/index.html', context)

@staff_member_required(login_url='dangnhap')
def duyetdonhang(request, donhang_id):
    if request.method == 'POST':
        dh = DONHANG.objects.get(id = donhang_id)
        dh.trangthai = 2
        dh.save()
        messages.success(request, "Cập nhật thành công")
    return redirect('quanlydonhang')
    
@staff_member_required(login_url='dangnhap')
def chitietdonhang(request, donhang_id):
    don_hang = DONHANG.objects.get(id = donhang_id)
    chitiet = CHITIETDONHANG.objects.filter(donhang = don_hang)
    context = {'chitiet': chitiet}
    return render(request, 'admin/donhang/chitietdonhang.html', context)

@staff_member_required(login_url='dangnhap')
def xoadonhang(request, donhang_id):
    if request.method == 'POST':
        donhang = DONHANG.objects.get(id = donhang_id)
        donhang.delete()
        messages.success(request, "Xóa thành công")
    return redirect('quanlydonhang')

@staff_member_required(login_url='dangnhap')
def quanlyloai(request):
    loai = LOAI.objects.all()
    context = {'loai': loai}
    return render(request, 'admin/loaisp/index.html', context)

@staff_member_required(login_url='dangnhap')
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

@staff_member_required(login_url='dangnhap')
def xoaloai(request, loai_id):
    if request.method == 'POST':
        loaisp = LOAI.objects.get(id = loai_id)
        loaisp.delete()
        messages.success(request, "Xoa thanh cong")
    return redirect('quanlyloai')

@staff_member_required(login_url='dangnhap')
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

@staff_member_required(login_url='dangnhap')
def quanlycuahang(request):
    cuahang = CUAHANG.objects.all()
    context = {'cuahang': cuahang}
    return render(request, 'admin/cuahang/index.html', context)

@staff_member_required(login_url='dangnhap')
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
            lon = lonch
        )
        cuahang.save()
        messages.success(request, "Thêm thành công")
        return redirect('quanlycuahang')    
    return render(request, 'admin/cuahang/themcuahang.html')

@staff_member_required(login_url='dangnhap')
def suacuahang(request, cuahang_id):
    cuahang = CUAHANG.objects.get(id = cuahang_id)
    if request.method == 'POST':
        cuahang.ten = request.POST.get('ten')
        cuahang.diachi = request.POST.get('diachi')
        cuahang.lat = request.POST.get('lat')
        cuahang.lon = request.POST.get('lon')
        cuahang.save()
        return redirect('quanlycuahang')
    context = {'cuahang': cuahang}
    return render(request, 'admin/cuahang/suacuahang.html', context)

@staff_member_required(login_url='dangnhap')
def xoacuahang(request, cuahang_id):
    cuahang = CUAHANG.objects.get(id = cuahang_id)
    if request.method == 'POST':
        cuahang.delete()
        messages.success(request, "Xóa thành công")
    return redirect('quanlycuahang')
def map_view(request):

    cuahang = CUAHANG.objects.all()

    data = []

    for ch in cuahang:
        data.append({
            "ten": ch.ten,
            "lat": ch.lat,
            "lon": ch.lon,
            "diachi": ch.diachi
        })

    context = {
        "stores_json": json.dumps(data, cls=DjangoJSONEncoder),
        "cuahang": cuahang
    }

    return render(request, "map.html", context)