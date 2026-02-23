from django.urls import path
from . import views

urlpatterns = [
    path('initiate/<int:order_id>/', views.initiate_payment),
    path('success/<int:payment_id>/', views.payment_success),
    path('failed/<int:payment_id>/', views.payment_failed),
]
