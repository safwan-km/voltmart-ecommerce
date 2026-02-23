from django.shortcuts import render
from django.shortcuts import get_object_or_404

# Create your views here.

from django.shortcuts import render
from .models import Product

def home(request):
    products = Product.objects.filter(is_active=True,category__is_active=True)
    return render(request, 'index.html', {
        'products': products
    })


def product_detail(request, slug):
    product = get_object_or_404(
    Product,
    slug=slug,
    is_active=True,
    category__is_active=True
)
    return render(request, 'product.html', {
        'product': product
    })


