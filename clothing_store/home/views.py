from django.shortcuts import render
from .models import SANPHAM
# Create your views here.
def get_home(request):
    sanpham = SANPHAM.objects.all()
    return render(request,'home/home.html',{'sanpham':sanpham})