from django.contrib import admin
from .models import Category, Produce, Order

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']

@admin.register(Produce)
class ProduceAdmin(admin.ModelAdmin):
    list_display = ['name', 'farmer', 'category', 'quantity', 'price', 'status', 'created_at']
    list_filter = ['status', 'category', 'created_at']
    search_fields = ['name', 'farmer__username', 'location']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'buyer', 'produce', 'quantity', 'total_price', 'status', 'payment_status', 'order_date']
    list_filter = ['status', 'payment_status', 'order_date']
    search_fields = ['order_number', 'buyer__username', 'mpesa_receipt']