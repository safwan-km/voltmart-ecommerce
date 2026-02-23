from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in

from cart.utils import merge_session_cart_to_user_cart


@receiver(user_logged_in)
def merge_cart_on_login(sender, request, user, **kwargs):
    merge_session_cart_to_user_cart(request)
