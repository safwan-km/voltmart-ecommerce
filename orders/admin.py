from django.contrib import admin
from .models import Address,Order, OrderItem

# Register your models here.

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'city', 'state', 'is_default')
    list_filter = ('state', 'city', 'is_default')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'original_amount',
        'discount_amount',
        'final_amount',
        'applied_coupon',
        'order_status',
        'created_at',
    )
    list_filter = ('order_status', 'created_at')
    search_fields = ('user__username', 'id')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'price', 'quantity')
    
from .models import CouponUsage

@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ('user', 'coupon', 'usage_count')

