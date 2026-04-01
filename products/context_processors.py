from .models import Category

def navbar_categories(request):
    return {
        "navbar_categories": Category.objects.filter(is_active=True)[:6]
    }
    
from .models import Wishlist

def wishlist_count(request):
    if request.user.is_authenticated:
        count = Wishlist.objects.filter(user=request.user).count()
    else:
        count = 0

    return {
        "wishlist_count": count
    }