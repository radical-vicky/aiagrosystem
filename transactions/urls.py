from django.urls import path
from . import views

urlpatterns = [
    path('payment/initiate/<int:order_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment/status/<int:payment_id>/', views.payment_status, name='payment_status'),
    path('payment/cancel/<int:payment_id>/', views.cancel_payment, name='cancel_payment'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
]