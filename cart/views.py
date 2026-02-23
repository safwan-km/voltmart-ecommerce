from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render,redirect

from products.models import Product
from orders.models import Address
from .utils import (
    add_to_session_cart,
    remove_from_session_cart,
    add_to_user_cart,
    remove_from_user_cart,
    get_session_cart,
    get_or_create_user_cart
)


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))


    if request.user.is_authenticated:
        add_to_user_cart(request.user, product.id, quantity)
    else:
        add_to_session_cart(request, product.id, quantity)

    return redirect('cart_page')

    


def remove_from_cart(request, product_id):
    if request.user.is_authenticated:
        remove_from_user_cart(request.user, product_id)
    else:
        remove_from_session_cart(request, product_id)

    return JsonResponse({
        "message": "Product removed from cart"
    })


def cart_summary(request):
    items = []
    total = 0

    if request.user.is_authenticated:
        cart = get_or_create_user_cart(request.user)

        for item in cart.items.all():
            subtotal = item.product.price * item.quantity
            total += subtotal

            items.append({
                "product": item.product.name,
                "quantity": item.quantity,
                "price": str(item.product.price),
                "subtotal": str(subtotal)
            })

    else:
        session_cart = get_session_cart(request)

        for product_id, quantity in session_cart.items():
            product = Product.objects.get(id=product_id)
            subtotal = product.price * quantity
            total += subtotal

            items.append({
                "product": product.name,
                "quantity": quantity,
                "price": str(product.price),
                "subtotal": str(subtotal)
            })

    return JsonResponse({
        "items": items,
        "total": str(total)
    })


def cart_page(request):
    items = []
    total = 0

    if request.user.is_authenticated:
        cart = get_or_create_user_cart(request.user)

        for item in cart.items.all():
            subtotal = item.product.price * item.quantity
            total += subtotal

            items.append({
                "product": item.product,
                "quantity": item.quantity,
                "price": item.product.price,
                "subtotal": subtotal,
            })
    else:
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

