from products.models import Product
from .models import CartItem
from .utils import get_session_cart, get_or_create_user_cart


def cart_data(request):

    cart_items = []
    cart_count = 0
    cart_total = 0

    # ---------- Logged in user cart ----------
    if request.user.is_authenticated:

        cart = get_or_create_user_cart(request.user)
        items = CartItem.objects.filter(cart=cart)

        for item in items:
            subtotal = item.product.price * item.quantity

            cart_items.append({
                "product": item.product,
                "quantity": item.quantity,
                "price": item.product.price,
                "subtotal": subtotal
            })

            cart_count += item.quantity
            cart_total += subtotal

    # ---------- Guest session cart ----------
    else:

        session_cart = get_session_cart(request)

        for product_id, quantity in session_cart.items():

            product = Product.objects.get(id=product_id)
            subtotal = product.price * quantity

            cart_items.append({
                "product": product,
                "quantity": quantity,
                "price": product.price,
                "subtotal": subtotal
            })

            cart_count += quantity
            cart_total += subtotal

    return {
        "cart_items": cart_items,
        "cart_count": cart_count,
        "cart_total": cart_total
    }