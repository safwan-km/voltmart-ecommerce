from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.urls import reverse

from cart.models import CartItem
from products.models import Product
from orders.models import Address

from .services import calculate_cart_totals

from .utils import (
    get_session_cart,
    add_to_session_cart,
    remove_from_session_cart,
    get_or_create_user_cart,
    add_to_user_cart,
    remove_from_user_cart
)
    


def add_to_cart(request, product_id):

    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))

    # Calculate current quantity in cart to prevent stock overflow
    current_qty = 0
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(cart__user=request.user, cart__is_active=True, product=product)
        if cart_items.exists():
            current_qty = cart_items.first().quantity
    else:
        session_cart = request.session.get("cart", {})
        current_qty = session_cart.get(str(product.id), 0)

    # Validate stock
    if current_qty + quantity > product.stock:
        return JsonResponse({
            "success": False,
            "error_msg": f"Stock limit reached. Only {product.stock - current_qty} more available."
        })

    # Proceed if valid
    if request.user.is_authenticated:
        add_to_user_cart(request.user, product.id, quantity)
        cart_items = CartItem.objects.filter(cart__user=request.user)
        cart_count = sum(item.quantity for item in cart_items)
    else:
        add_to_session_cart(request, product.id, quantity)
        session_cart = request.session.get("cart", {})
        cart_count = sum(session_cart.values())

    return JsonResponse({
        "success": True,
        "cart_count": cart_count
    })


def remove_from_cart(request, product_id):

    if request.user.is_authenticated:
        remove_from_user_cart(request.user, product_id)
    else:
        remove_from_session_cart(request, product_id)

    # Redirect back to the previous page
    return redirect(request.META.get("HTTP_REFERER", "home"))


def cart_summary(request):
    cart_items = []
    total = 0

    if request.user.is_authenticated:
        cart = get_or_create_user_cart(request.user)

        for item in cart.items.all():
            subtotal = item.product.price * item.quantity
            total += subtotal

            cart_items.append({
                "product": item.product,
                "quantity": item.quantity,
                "subtotal": subtotal
            })

    else:
        session_cart = get_session_cart(request)

        for product_id, quantity in session_cart.items():
            product = Product.objects.get(id=product_id)
            subtotal = product.price * quantity
            total += subtotal

            cart_items.append({
                "product": product,
                "quantity": quantity,
                "subtotal": subtotal
            })

    context = {
        "cart_items": cart_items,
        "cart_total": total,
        "cart_count": sum(item["quantity"] for item in cart_items)
    }

    html = render_to_string("cart/cart_dropdown.html", context, request=request)

    return HttpResponse(html)


def cart_page(request):
    if request.user.is_authenticated:
        cart_items, subtotal = calculate_cart_totals(request.user)

        items = [
            {
                "product": item.product,
                "quantity": item.quantity,
                "price": item.product.price,
                "subtotal": item.product.price * item.quantity,
            }
            for item in cart_items
        ]

        total = subtotal

    else:
        items = []
        total = 0
        session_cart = get_session_cart(request)

        for product_id, quantity in session_cart.items():
            product = Product.objects.get(id=product_id)
            subtotal = product.price * quantity
            total += subtotal

            items.append({
                "product": product,
                "quantity": quantity,
                "price": product.price,
                "subtotal": subtotal,
            })

    return render(request, "cart.html", {
        "items": items,
        "total": total
    })


def update_cart(request, product_id):
    action = request.POST.get("action")

    if request.user.is_authenticated:
        cart = get_or_create_user_cart(request.user)
        item = cart.items.get(product_id=product_id)

        if action == "increase":
            item.quantity += 1
        elif action == "decrease" and item.quantity > 1:
            item.quantity -= 1

        item.save()

    else:
        cart = get_session_cart(request)
        product_id = str(product_id)

        if product_id not in cart:
            cart[product_id] = 1

        if action == "increase":
            cart[product_id] += 1
        elif action == "decrease" and cart[product_id] > 1:
            cart[product_id] -= 1

        request.session.modified = True

    return redirect("cart_page")


def buy_now(request, product_id):

    product = get_object_or_404(Product, id=product_id)

    # Save the target product for the single-item checkout flow
    request.session["buy_now_product_id"] = product.id

    return redirect(reverse("checkout") + "?buy_now=true")
