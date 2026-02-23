from django.urls import path
from . import views

urlpatterns = [
    path('', views.cart_page, name='cart_page'),   # CART PAGE
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path("update/<int:product_id>/", views.update_cart, name="update_cart"),
    path('summary/', views.cart_summary, name='cart_summary'),
]
