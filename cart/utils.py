from products.models import Product
from .models import Cart, CartItem


# ---------- SESSION CART (GUEST USER) ----------

def get_session_cart(request):
    """
    Returns session cart dictionary.
    Example: {'1': 2, '5': 1}
    """
    return request.session.get('cart', {})


def add_to_session_cart(request, product_id, quantity=1):
    cart = get_session_cart(request)
    product_id = str(product_id)

    if product_id in cart:
        cart[product_id] += quantity
    else:
        cart[product_id] = quantity

    request.session['cart'] = cart
    request.session.modified = True


def remove_from_session_cart(request, product_id):
    cart = get_session_cart(request)
    product_id = str(product_id)

    if product_id in cart:
        del cart[product_id]
        request.session['cart'] = cart
        request.session.modified = True


# ---------- DATABASE CART (LOGGED-IN USER) ----------

def get_or_create_user_cart(user):
    cart, created = Cart.objects.get_or_create(user=user, is_active=True)
    return cart


def add_to_user_cart(user, product_id, quantity=1):
    cart = get_or_create_user_cart(user)
    product = Product.objects.get(id=product_id)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product
    )

    if created:
        cart_item.quantity = quantity
    else:
        cart_item.quantity += quantity

    cart_item.save()


def remove_from_user_cart(user, product_id):
    cart = get_or_create_user_cart(user)
    CartItem.objects.filter(cart=cart, product_id=product_id).delete()


# ---------- MERGE SESSION CART INTO USER CART ----------

def merge_session_cart_to_user_cart(request):
    """
    Called AFTER user logs in.
    """
    session_cart = get_session_cart(request)

    if not session_cart:
        return

    for product_id, quantity in session_cart.items():
        add_to_user_cart(request.user, product_id, quantity)

    # Clear session cart
    request.session.pop('cart', None)
    request.session.modified = True
