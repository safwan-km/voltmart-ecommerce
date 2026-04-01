from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from .models import Coupon, CouponUsage
from decimal import Decimal


def validate_coupon(code, user, subtotal):
    """
    Validates coupon and returns (coupon_obj, discount_amount)
    Raises ValueError if invalid.
    """

    try:
        coupon = Coupon.objects.get(code__iexact=code.strip())
    except Coupon.DoesNotExist:
        raise ValueError("Invalid coupon code.")

    if not coupon.is_valid():
        raise ValueError("Coupon is expired or inactive.")

    # Check per-user usage
    usage = CouponUsage.objects.filter(user=user, coupon=coupon).first()

    if usage and usage.usage_count >= coupon.per_user_limit:
        raise ValueError("Coupon usage limit reached.")

    if subtotal <= 0:
        raise ValueError("Cart total must be greater than zero.")

    # Calculate discount
    if coupon.discount_type == "PERCENTAGE":
        discount = (subtotal * coupon.discount_value) / Decimal("100")
    else:
        discount = coupon.discount_value
        

    # Never allow negative total
    if discount > subtotal:
        discount = subtotal
        
    discount = discount.quantize(Decimal("0.01"))

    return coupon, discount 