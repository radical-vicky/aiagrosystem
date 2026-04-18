# transactions/admin.py

from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['reference', 'user', 'order', 'amount', 'transaction_type', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'transaction_type', 'payment_method', 'created_at']
    search_fields = ['reference', 'user__username', 'user__email', 'mpesa_receipt', 'order__order_number']
    readonly_fields = ['reference', 'checkout_request_id', 'mpesa_response', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('reference', 'user', 'order', 'amount', 'transaction_type', 'status')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'mpesa_receipt', 'checkout_request_id', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Raw Response', {
            'fields': ('mpesa_response',),
            'classes': ('collapse',)
        }),
    )