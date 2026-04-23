from django.http import JsonResponse
from django.shortcuts import redirect, render,get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product,Category,HeroBanner,NewsletterSubscriber,Wishlist
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_POST


def home(request):

    banner = HeroBanner.objects.filter(is_active=True).order_by('-created_at').first()

    products = Product.objects.filter(
        is_active=True,
        category__is_active=True
    ).select_related('category').order_by('-created_at')[:8]

    featured_products = Product.objects.filter(
        is_active=True,
        is_featured=True
    ).select_related('category')[:8]

    categories = Category.objects.filter(
        is_active=True,
        is_featured=True
    )[:3]

    user_wishlist = []
    if request.user.is_authenticated:
        user_wishlist = list(Wishlist.objects.filter(user=request.user).values_list("product_id", flat=True))

    context = {
        'banner': banner,
        'products': products,
        'featured_products': featured_products,
        'categories': categories,
        'user_wishlist': user_wishlist
    }

    return render(request, 'index.html', context)


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
    
    
# This view is for the store page, which lists all active products.
def store(request):

    products = Product.objects.filter(is_active=True)
    categories = Category.objects.filter(is_active=True)
    category_slug = request.GET.get('category') or ''
    query = request.GET.get('q') or ''
    min_price = request.GET.get('min_price') or ''
    max_price = request.GET.get('max_price') or ''
    sort = request.GET.get('sort') or ''

    # Guard against literal "None" strings sent by pagination links
    if category_slug == 'None': category_slug = ''
    if min_price == 'None': min_price = ''
    if max_price == 'None': max_price = ''
    if sort == 'None': sort = ''
    
    if query:
        products = products.filter(Q(name__icontains=query) |Q(description__icontains=query))

    if category_slug:
        products = products.filter(category__slug=category_slug)

    if min_price:
        products = products.filter(price__gte=min_price)

    if max_price:
        products = products.filter(price__lte=max_price)

    # Sorting
    if sort == "price_low":
        products = products.order_by("price")

    elif sort == "price_high":
        products = products.order_by("-price")

    elif sort == "newest":
        products = products.order_by("-created_at")

    paginator = Paginator(products, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    user_wishlist = []
    if request.user.is_authenticated:
        user_wishlist = list(Wishlist.objects.filter(user=request.user).values_list("product_id", flat=True))

    context = {
        "products": page_obj,
        "page_obj": page_obj,
        "categories": categories,
        "selected_category": category_slug,
        "min_price": min_price,
        "max_price": max_price,
        "selected_sort": sort,
        "query": query,
        "user_wishlist": user_wishlist
    }

    return render(request, "store.html", context)

def subscribe_newsletter(request):
    if request.method == "POST":
        email = request.POST.get("email")

        if email:
            NewsletterSubscriber.objects.get_or_create(email=email)
            return JsonResponse({"success": True, "message": "Subscribed successfully!"})

    return JsonResponse({"success": False, "message": "Subscription failed."})


@require_POST
def toggle_wishlist(request, product_id):

    if not request.user.is_authenticated:
        return JsonResponse({"status": "login_required"}, status=401)

    product = get_object_or_404(Product, id=product_id)

    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    if not created:
        wishlist_item.delete()
        status = "removed"
    else:
        status = "added"

    wishlist_count = Wishlist.objects.filter(user=request.user).count()

    return JsonResponse({
        "status": status,
        "wishlist_count": wishlist_count
    })

@login_required
def wishlist_page(request):

    wishlist_items = (
        Wishlist.objects
        .filter(user=request.user)
        .select_related("product")
    )

    user_wishlist = list(
        wishlist_items.values_list("product_id", flat=True)
    )
    

    context = {
        "wishlist_items": wishlist_items,
        "user_wishlist": user_wishlist,
    }

    return render(request, "wishlist.html", context)