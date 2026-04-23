from django.urls import path
from . import views

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('address/add/', views.add_address, name='add_address'),
    path('address/edit/<int:address_id>/', views.edit_address, name='edit_address'),
    path('orders/', views.order_history, name='order_history'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('profile/addresses/', views.address_list, name='address_list'),
    path('profile/addresses/delete/<int:address_id>/', views.delete_address, name='delete_address'),
    path('success/<int:order_id>/', views.order_success, name='order_success'),
    path('cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('simulate-payment/<int:order_id>/', views.simulate_payment, name='simulate_payment'),




]
