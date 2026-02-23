from django.shortcuts import render,redirect

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib import messages


from cart.utils import get_or_create_user_cart
from .models import Order, OrderItem, Address

# Create your views here.

@login_required
def checkout(request):
    user = request.user
    cart = get_or_create_user_cart(user)
    cart_items = cart.items.all()
    
    print("CART:", cart)
    print("CART ITEMS COUNT:", cart_items.count())


    if not cart_items.exists():
        return redirect('cart_page')

    addresses = Address.objects.filter(user=user)

    total_amount = sum(
        item.product.price * item.quantity for item in cart_items
    )

    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        address = get_object_or_404(Address, id=address_id, user=user)

        payment_method = request.POST.get('payment_method', 'COD')

        order = Order.objects.create(
            user=user,
            address=address,
            total_amount=total_amount,
            payment_method=payment_method,
            status='PENDING'
        )


        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity
            )

        cart.items.all().delete()  # clear cart after order

        return redirect('order_success', order_id=order.id)

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'addresses': addresses,
        'total_amount': total_amount,
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


