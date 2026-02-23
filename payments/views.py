from django.shortcuts import render

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

from orders.models import Order
from cart.models import CartItem
from .models import Payment

# Create your views here.

@login_required
def initiate_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status != 'PENDING':
        return JsonResponse({"error": "Invalid order status"}, status=400)

    # Create payment attempt
    payment = Payment.objects.create(
        order=order,
        amount=order.total_amount,
        status='INITIATED'
    )

    return JsonResponse({
        "message": "Payment initiated",
        "payment_id": payment.id,
        "order_id": order.id,
        "amount": str(order.total_amount)
    })


@login_required
def payment_success(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    order = payment.order

    if order.user != request.user:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    # Update payment
    payment.status = 'SUCCESS'
    payment.save()

    # Update order
    order.status = 'PAID'
    order.save()

    # Reduce stock
    for item in order.items.all():
        product = item.product
        product.stock -= item.quantity
        product.save()

    # Clear cart
    CartItem.objects.filter(cart__user=request.user).delete()

    return JsonResponse({
        "message": "Payment successful",
        "order_id": order.id
    })


@login_required
def payment_failed(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    order = payment.order

    if order.user != request.user:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    payment.status = 'FAILED'
    payment.save()

    order.status = 'FAILED'
    order.save()

    return JsonResponse({
        "message": "Payment failed",
        "order_id": order.id
    })

