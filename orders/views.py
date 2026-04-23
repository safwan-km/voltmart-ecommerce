from urllib import request

from django.shortcuts import render,redirect

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
import json
from django.http import JsonResponse
from django.contrib import messages


from cart.utils import get_or_create_user_cart
from cart.models import CartItem
from payments.models import Payment
from .models import Coupon, CouponUsage, Order, OrderItem, Address
from cart.services import calculate_cart_totals
from orders.services import validate_coupon
import razorpay
from django.conf import settings


# Create your views here.

from products.models import Product

@login_required
def checkout(request):
    user = request.user

    is_buy_now = request.GET.get('buy_now') == 'true' or request.POST.get('is_buy_now') == 'true'

    if is_buy_now:
        buy_now_product_id = request.session.get('buy_now_product_id')
        if not buy_now_product_id:
            return redirect('cart_page')
        
        product = get_object_or_404(Product, id=buy_now_product_id)
        
        class MockCartItem:
            def __init__(self, product):
                self.product = product
                self.quantity = 1
                
        cart_items = [MockCartItem(product)]
        subtotal = product.price
    else:
        cart_items, subtotal = calculate_cart_totals(user)

        if not cart_items:
            return redirect('cart_page')

    addresses = Address.objects.filter(user=user)
    available_coupons = Coupon.objects.filter(is_active=True)

    discount_amount = 0
    applied_coupon = None

    # Revalidate session coupon
    coupon_id = request.session.get("applied_coupon_id")
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            applied_coupon, discount_amount = validate_coupon(
                coupon.code, user, subtotal
            )
        except:
            request.session.pop("applied_coupon_id", None)

    from django.urls import reverse
    redirect_url = reverse("checkout") + "?buy_now=true" if is_buy_now else "checkout"

    if request.method == "POST":

        # ---------------- REMOVE COUPON ----------------
        if "remove_coupon" in request.POST:
            request.session.pop("applied_coupon_id", None)
            return redirect(redirect_url)

        # ---------------- APPLY COUPON ----------------
        if "apply_coupon" in request.POST:
            code = request.POST.get("apply_coupon")

        elif "apply_coupon_manual" in request.POST:
            code = request.POST.get("coupon_code")

        else:
            code = None

        if code:
            try:
                coupon, discount_amount = validate_coupon(code, user, subtotal)
                request.session["applied_coupon_id"] = coupon.id
                applied_coupon = coupon
            except ValueError as e:
                messages.error(request, str(e))
                return redirect(redirect_url)

        # ---------------- PLACE ORDER ----------------
        if "place_order" in request.POST:
            address_id = request.POST.get('address_id')
            address = get_object_or_404(Address, id=address_id, user=user)
            payment_method = request.POST.get('payment_method', 'COD')

            # Revalidate again before order creation
            discount_amount = 0
            applied_coupon = None

            coupon_id = request.session.get("applied_coupon_id")
            if coupon_id:
                try:
                    coupon = Coupon.objects.get(id=coupon_id)
                    applied_coupon, discount_amount = validate_coupon(
                        coupon.code, user, subtotal
                    )
                except:
                    request.session.pop("applied_coupon_id", None)

            final_amount = subtotal - discount_amount

            order_status = 'CONFIRMED' if payment_method == 'COD' else 'PENDING'
            order = Order.objects.create(
                user=user,
                address=address,
                payment_method=payment_method,
                original_amount=subtotal,
                discount_amount=discount_amount,
                final_amount=final_amount,
                applied_coupon=applied_coupon,
                order_status=order_status,
                payment_status='PENDING'
            )

            if payment_method == 'COD':
                payment_status = 'PENDING'
                razorpay_order_id = None

            elif payment_method == 'UPI':
                client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

                razorpay_order = client.order.create({
                    "amount": int(final_amount * 100),
                    "currency": "INR",
                    "payment_capture": 1
                })

                razorpay_order_id = razorpay_order['id']
                payment_status = 'PENDING'

            else:
                payment_status = 'PENDING'
                razorpay_order_id = None

            Payment.objects.create(
                order=order,
                amount=final_amount,
                status=payment_status,
                razorpay_order_id=razorpay_order_id
            )

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity
                )

            if payment_method == 'COD' and applied_coupon:
                usage, created = CouponUsage.objects.get_or_create(
                    user=user,
                    coupon=applied_coupon
                )
                usage.usage_count += 1
                usage.save()

            if not is_buy_now:
                user.cart.items.all().delete()
            else:
                request.session.pop("buy_now_product_id", None)
            request.session.pop("applied_coupon_id", None)

            if payment_method == 'UPI':
                return render(request, 'razorpay_payment.html', {
                    'order': order,
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_key': settings.RAZORPAY_KEY_ID,
                    'amount': int(final_amount * 100),
                })
            else:
                return redirect('order_success', order_id=order.id)
            
        return redirect(redirect_url)

    final_amount = subtotal - discount_amount

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'addresses': addresses,
        'subtotal': subtotal,
        'discount_amount': discount_amount,
        'final_amount': final_amount,
        'applied_coupon': applied_coupon,
        'available_coupons': available_coupons,
        'is_buy_now': is_buy_now,
        
    })



@login_required
def add_address(request):
    next_url = request.GET.get('next', 'checkout')

    if request.method == 'POST':
        Address.objects.create(
            user=request.user,
            full_name=request.POST['full_name'],
            phone=request.POST['phone'],
            address_line_1=request.POST['address_line_1'],
            address_line_2=request.POST.get('address_line_2', ''),
            city=request.POST['city'],
            district=request.POST['district'],
            state=request.POST['state'],
            pincode=request.POST['pincode'],
        )
        return redirect(next_url)

    return render(request, 'add_address.html')


@login_required
def edit_address(request, address_id):
    address = get_object_or_404(
        Address,
        id=address_id,
        user=request.user
    )

    next_url = request.GET.get('next', 'checkout')

    if request.method == 'POST':
        address.full_name = request.POST['full_name']
        address.phone = request.POST['phone']
        address.address_line_1 = request.POST['address_line_1']
        address.address_line_2 = request.POST.get('address_line_2', '')
        address.city = request.POST['city']
        address.district = request.POST['district']
        address.state = request.POST['state']
        address.pincode = request.POST['pincode']
        address.save()

        return redirect(next_url)

    return render(request, 'edit_address.html', {
        'address': address
    })

@login_required
def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'address_list.html', {
        'addresses': addresses
    })
    

@login_required
def delete_address(request, address_id):
    if request.method != 'POST':
        return redirect('address_list')

    address = get_object_or_404(
        Address,
        id=address_id,
        user=request.user
    )

    order_exists = Order.objects.filter(address=address).exists()

    if order_exists:
        messages.error(request, "This address is used in an order and cannot be deleted.")
        return redirect('address_list')

    address.delete()

    messages.success(request, "Address deleted successfully.")
    return redirect('address_list')





# Order history view

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'order_history.html', {
        'orders': orders
    })

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    return render(request, 'order_detail.html', {
        'order': order
    })



def order_success(request, order_id):
    order = Order.objects.get(id=order_id, user=request.user)

    return render(request, 'order_success.html', {
        'order': order
    })

@login_required
def cancel_order(request, order_id):
    if request.method != 'POST':
        return redirect('order_detail', order_id=order_id)

    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Block cancel for orders that cannot be cancelled
    if order.order_status in ('CANCELLED', 'SHIPPED', 'DELIVERED'):
        messages.error(request, "This order cannot be cancelled.")
        return redirect('order_detail', order_id=order_id)

    # ── PAID → trigger Razorpay refund (or handle demo) ───────────────────
    if order.payment_status == 'PAID':
        payment = Payment.objects.filter(order=order).order_by('-created_at').first()

        is_demo = payment and payment.payment_id and payment.payment_id.startswith('demo_')

        if is_demo:
            # Demo/simulated payment — no real refund needed
            if payment:
                payment.status = 'REFUNDED'
                payment.save()
            order.payment_status = 'REFUNDED'
            refund_msg = "Your demo order has been cancelled. Items have been restored to your cart."

        elif payment and payment.payment_id:
            try:
                client = razorpay.Client(
                    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
                )
                refund_amount = int(order.final_amount * 100)   # paise
                client.payment.refund(payment.payment_id, {"amount": refund_amount})

                payment.status = 'REFUNDED'
                payment.save()

                order.payment_status = 'REFUNDED'
            except Exception as e:
                messages.error(
                    request,
                    f"Refund could not be initiated: {str(e)}. Please contact support."
                )
                return redirect('order_detail', order_id=order_id)

            refund_msg = (
                "Your order has been cancelled and a refund of "
                f"₹{order.final_amount} has been initiated. "
                "It will reflect in your account within 3–5 business days."
            )
        else:
            messages.error(request, "Payment record not found. Please contact support.")
            return redirect('order_detail', order_id=order_id)

    else:
        # ── COD / PENDING → plain cancel ──────────────────────────────────
        order.payment_status = 'FAILED'
        refund_msg = "Your order has been cancelled. Items have been restored to your cart."

    # Restore cart items
    cart = get_or_create_user_cart(request.user)
    for item in order.items.all():
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=item.product,
            defaults={'quantity': item.quantity}
        )
        if not created:
            cart_item.quantity += item.quantity
            cart_item.save()

    order.order_status = 'CANCELLED'
    order.save()

    messages.success(request, refund_msg)
    return redirect('cart_page')

    
@login_required
def payment_success(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    data = json.loads(request.body)

    order_id = data.get("order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_signature = data.get("razorpay_signature")

    order = get_object_or_404(Order, id=order_id, user=request.user)

    try:
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature,
        }
        client.utility.verify_payment_signature(params_dict)
    except razorpay.errors.SignatureVerificationError as e:
        return JsonResponse({"status": "failed", "error": "Signature verification failed."}, status=400)

    payment = Payment.objects.filter(order=order).order_by('-created_at').first()
    if payment:
        payment.payment_id = razorpay_payment_id
        payment.status = 'PAID'
        payment.save()

    order.payment_status = 'PAID'
    order.order_status = 'CONFIRMED'
    order.save()

    if order.applied_coupon:
        usage, created = CouponUsage.objects.get_or_create(
            user=request.user,
            coupon=order.applied_coupon
        )
        usage.usage_count += 1
        usage.save()
        request.session.pop("applied_coupon_id", None)

    CartItem.objects.filter(cart__user=request.user).delete()
    request.session.pop("buy_now_product_id", None)

    return JsonResponse({"status": "ok"})


@login_required
def simulate_payment(request, order_id):
    """
    Demo/Dev only: Simulates a successful payment without going through Razorpay.
    Used when Razorpay KYC is not completed or for portfolio demonstration.
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.order_status != 'PENDING' or order.payment_status != 'PENDING':
        messages.error(request, "This order cannot be simulated — it is already processed.")
        return redirect('order_detail', order_id=order.id)

    # Mark payment as paid
    payment = Payment.objects.filter(order=order).order_by('-created_at').first()
    if payment:
        payment.payment_id = f"demo_pay_{order.id}"
        payment.status = 'PAID'
        payment.save()

    order.payment_status = 'PAID'
    order.order_status = 'CONFIRMED'
    order.save()

    # Record coupon usage if applied
    if order.applied_coupon:
        usage, created = CouponUsage.objects.get_or_create(
            user=request.user,
            coupon=order.applied_coupon
        )
        usage.usage_count += 1
        usage.save()

    # Clear cart
    CartItem.objects.filter(cart__user=request.user).delete()
    request.session.pop("buy_now_product_id", None)

    messages.success(request, "Demo payment successful! Order confirmed.")
    return redirect('order_success', order_id=order.id)