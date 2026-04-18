# marketplace/urls.py

from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    path('', views.marketplace_home, name='marketplace'),
    path('produce/<int:pk>/', views.produce_detail, name='produce_detail'),
    path('produce/add/', views.add_produce, name='add_produce'),
    path('produce/<int:pk>/edit/', views.edit_produce, name='edit_produce'),
    path('produce/<int:pk>/delete/', views.delete_produce, name='delete_produce'),
    path('produce/<int:pk>/order/', views.place_order, name='place_order'),
    path('order/<int:pk>/', views.order_detail, name='order_detail'),
    path('order/<int:pk>/cancel/', views.cancel_order, name='cancel_order'),
    path('category/<int:category_id>/products/', views.products_by_category, name='products_by_category'),
    path('api/featured-products/', views.get_featured_products, name='get_featured_products'),
    path('produce/<int:pk>/delete/', views.delete_produce_confirmation, name='delete_produce'),
    path('produce/<int:pk>/delete/confirm/', views.delete_produce, name='delete_produce_confirm'),

]