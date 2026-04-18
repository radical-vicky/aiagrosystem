# transactions/urls.py

from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('pay/<int:order_id>/', views.initiate_payment, name='initiate_payment'),
    path('status/<int:transaction_id>/', views.check_payment_status, name='check_payment_status'),
    path('cancel/<int:transaction_id>/', views.cancel_payment, name='cancel_payment'),
    path('callback/', views.mpesa_callback, name='mpesa_callback'),
    path('history/', views.transaction_history, name='transaction_history'),
    path('check-status/<int:transaction_id>/', views.check_status_ajax, name='check_status_ajax'),
    
]