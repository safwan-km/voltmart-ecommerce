from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('store/', views.store, name='store'),
    path("subscribe-newsletter/", views.subscribe_newsletter, name="subscribe_newsletter"),
    path("wishlist/toggle/<int:product_id>/",views.toggle_wishlist,name="toggle_wishlist"),
    path("wishlist/", views.wishlist_page, name="wishlist_page"),
]
