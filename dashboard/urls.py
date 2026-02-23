from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardHomeView.as_view(), name="home"),
    #orders
    path("orders/", views.OrderListView.as_view(), name="orders"),
    path("orders/<int:pk>/", views.OrderDetailView.as_view(), name="order_detail"),
    #products
    path("products/", views.ProductListView.as_view(), name="products"),
    path("products/create/", views.ProductCreateView.as_view(), name="product_create"),
    path("products/<int:pk>/edit/", views.ProductUpdateView.as_view(), name="product_edit"),
    path("products/<int:pk>/toggle/", views.ProductToggleStatusView.as_view(), name="product_toggle"),
    path("products/<int:pk>/delete/", views.ProductSafeDeleteView.as_view(), name="product_delete"),
    #categories
    path("categories/", views.CategoryListView.as_view(), name="categories"),
    path("categories/create/", views.CategoryCreateView.as_view(), name="category_create"),
    path("categories/<int:pk>/edit/", views.CategoryUpdateView.as_view(), name="category_edit"),
    path("categories/<int:pk>/toggle/", views.CategoryToggleStatusView.as_view(), name="category_toggle"),
    path("categories/<int:pk>/delete/", views.CategorySafeDeleteView.as_view(), name="category_delete"),
    #users
    path("users/", views.UserListView.as_view(), name="users"),
    path("users/<int:pk>/", views.UserDetailView.as_view(), name="user_detail"),
    path("users/<int:pk>/toggle/", views.UserToggleStatusView.as_view(), name="user_toggle"),
    path("users/<int:pk>/toggle-staff/", views.UserToggleStaffView.as_view(), name="user_toggle_staff"),
    
    #Coupons
    path("coupons/", views.CouponListView.as_view(), name="coupons"),
    path("coupons/create/", views.CouponCreateView.as_view(), name="coupon_create"),
    path("coupons/<int:pk>/edit/", views.CouponUpdateView.as_view(), name="coupon_edit"),
    path("coupons/<int:pk>/toggle/", views.CouponToggleStatusView.as_view(), name="coupon_toggle"),
    path("coupons/<int:pk>/delete/", views.CouponDeleteView.as_view(), name="coupon_delete"),

    #reports
    path("reports/", views.ReportsView.as_view(), name="reports"),

    






    # path('orders/', views.order_list, name='orders'),
    # path('products/', views.product_list, name='products'),
    # path('users/', views.user_list, name='users'),
    # path('categories/', views.category_list, name='categories'),
    # path('reports/', views.report_list, name='reports'),
    # path('coupons/', views.coupon_list, name='coupons'),
]
