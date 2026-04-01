from decimal import Decimal
from .utils import get_or_create_user_cart


def calculate_cart_totals(user):
    """
    Centralized cart calculation.
    Returns:
        cart_items (QuerySet)
        subtotal (Decimal)
    """
    cart = get_or_create_user_cart(user)
    cart_items = cart.items.select_related("product")

    subtotal = Decimal("0.00")

    for item in cart_items:
        subtotal += item.product.price * item.quantity

    return cart_items, subtotal