from .models import Category

def navbar_categories(request):
    categories = Category.objects.filter(is_active=True)
    return {
        "navbar_categories": categories[:6],
        "categories": categories
        
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