from urllib import request

from django.shortcuts import render,redirect

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib import messages


from cart.utils import get_or_create_user_cart
from .models import Coupon, CouponUsage, Order, OrderItem, Address
from cart.services import calculate_cart_totals
from orders.services import validate_coupon

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

            order = Order.objects.create(
                user=user,
                address=address,
                payment_method=payment_method,
                original_amount=subtotal,
                discount_amount=discount_amount,
                final_amount=final_amount,
                applied_coupon=applied_coupon,
                status='PENDING'
            )

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity
                )

            # Update usage
            if applied_coupon:
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
    print("DELETE VIEW HIT")

    if request.method != 'POST':
        print("Not POST request")
        return redirect('address_list')

    address = get_object_or_404(
        Address,
        id=address_id,
        user=request.user
    )

    order_exists = Order.objects.filter(address=address).exists()
    print("Order exists:", order_exists)

    if order_exists:
        messages.error(request, "This address is used in an order and cannot be deleted.")
        return redirect('address_list')

    address.delete()
    print("Address deleted")

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


