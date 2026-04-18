# transactions/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import datetime, timedelta
import json

from .models import Transaction
from .mpesa import mpesa_api
from marketplace.models import Order


@login_required
def initiate_payment(request, order_id):
    """Initiate M-Pesa payment for an order"""
    order = get_object_or_404(Order, pk=order_id, buyer=request.user)
    
    if order.payment_status == 'paid':
        messages.error(request, 'This order has already been paid.')
        return redirect('order_detail', pk=order.id)
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        
        if not phone_number:
            messages.error(request, 'Please enter your M-Pesa phone number.')
            return redirect('initiate_payment', order_id=order.id)
        
        # Format phone number
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('+'):
            phone_number = phone_number[1:]
        elif not phone_number.startswith('254'):
            phone_number = '254' + phone_number
        
        # Create transaction
        transaction = Transaction.objects.create(
            user=request.user,
            order=order,
            amount=order.total_price,
            transaction_type='payment',
            status='pending',
            payment_method='mpesa',
            description=f'Payment for Order {order.order_number}'
        )
        
        # Initiate STK Push
        result = mpesa_api.stk_push(
            phone_number=phone_number,
            amount=float(order.total_price),
            account_reference=f"ORDER{order.id}",
            transaction_desc=f"Payment for Order {order.order_number}"
        )
        
        if result and result.get('ResponseCode') == '0':
            transaction.checkout_request_id = result.get('CheckoutRequestID')
            transaction.mpesa_response = result
            transaction.save()
            
            request.session['checkout_request_id'] = result.get('CheckoutRequestID')
            request.session['transaction_id'] = transaction.id
            
            messages.info(request, 'Please check your phone and enter your M-Pesa PIN.')
            return redirect('transactions:check_payment_status', transaction_id=transaction.id)
        else:
            transaction.status = 'failed'
            transaction.mpesa_response = result
            transaction.save()
            error_msg = result.get('errorMessage', 'Payment initiation failed') if result else 'Payment service unavailable'
            messages.error(request, f'Payment failed: {error_msg}')
            return redirect('order_detail', pk=order.id)
    
    return render(request, 'transactions/initiate_payment.html', {'order': order})

# In transactions/views.py, update the check_payment_status function:

@login_required
def check_payment_status(request, transaction_id):
    """Check payment status"""
    transaction = get_object_or_404(Transaction, pk=transaction_id, user=request.user)
    
    # If already completed, show success page immediately
    if transaction.status == 'completed':
        return render(request, 'transactions/payment_status.html', {
            'transaction': transaction,
            'checkout_request_id': transaction.checkout_request_id
        })
    
    # If cancelled or failed, show appropriate page
    if transaction.status in ['cancelled', 'failed']:
        return render(request, 'transactions/payment_status.html', {
            'transaction': transaction,
            'checkout_request_id': transaction.checkout_request_id
        })
    
    # Check payment status with M-Pesa
    checkout_request_id = transaction.checkout_request_id
    
    if not checkout_request_id:
        messages.error(request, 'No active payment session found.')
        return redirect('transactions:initiate_payment', order_id=transaction.order.id)
    
    result = mpesa_api.check_payment_status(checkout_request_id)
    
    if result:
        if result.get('ResultCode') == '0':
            # Payment successful
            transaction.status = 'completed'
            transaction.mpesa_receipt = result.get('MpesaReceiptNumber')
            transaction.completed_at = timezone.now()
            transaction.mpesa_response = result
            transaction.save()
            
            order = transaction.order
            order.payment_status = 'paid'
            order.payment_method = 'mpesa'
            order.payment_reference = transaction.reference
            order.mpesa_receipt = result.get('MpesaReceiptNumber')
            order.estimated_delivery_date = timezone.now().date() + timedelta(days=5)
            order.save()
            
        elif result.get('ResultCode') == '1037':
            # User cancelled
            transaction.status = 'cancelled'
            transaction.mpesa_response = result
            transaction.save()
            
        elif result.get('ResultCode') in ['1032', '1033', '1034']:
            # Insufficient funds or transaction failed
            transaction.status = 'failed'
            transaction.mpesa_response = result
            transaction.save()
        else:
            # Still pending or other status
            # Don't change status, just show pending
            pass
    
    return render(request, 'transactions/payment_status.html', {
        'transaction': transaction,
        'checkout_request_id': checkout_request_id
    })
@csrf_exempt
def mpesa_callback(request):
    """M-Pesa payment callback"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            result_code = data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
            checkout_request_id = data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
            
            transaction = Transaction.objects.filter(checkout_request_id=checkout_request_id).first()
            
            if transaction:
                if result_code == '0':
                    transaction.status = 'completed'
                    transaction.completed_at = timezone.now()
                    transaction.save()
                    
                    order = transaction.order
                    order.payment_status = 'paid'
                    order.save()
            
            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})
        except Exception as e:
            return JsonResponse({'ResultCode': 1, 'ResultDesc': str(e)})
    
    return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Method not allowed'})


@login_required
def transaction_history(request):
    """View transaction history"""
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'transactions/history.html', {'transactions': transactions})




@login_required
def cancel_payment(request, transaction_id):
    """Cancel pending payment"""
    transaction = get_object_or_404(Transaction, pk=transaction_id, user=request.user)
    
    if transaction.status == 'pending':
        transaction.status = 'cancelled'
        transaction.save()
        
        # Also cancel the associated order if needed
        order = transaction.order
        if order.status == 'pending' and order.payment_status != 'paid':
            order.status = 'cancelled'
            order.save()
            
            # Restore produce quantity
            produce = order.produce
            produce.quantity += order.quantity
            if produce.status == 'sold_out':
                produce.status = 'available'
            produce.save()
        
        messages.success(request, 'Payment has been cancelled successfully.')
    else:
        messages.error(request, 'This payment cannot be cancelled.')
    
    # Fix: Use direct path instead of URL name
    return redirect(f'/marketplace/order/{transaction.order.id}/')

from django.http import JsonResponse

@login_required
def check_status_ajax(request, transaction_id):
    """AJAX endpoint to check payment status"""
    transaction = get_object_or_404(Transaction, pk=transaction_id, user=request.user)
    
    # If already completed, failed, or cancelled
    if transaction.status != 'pending':
        return JsonResponse({'status': transaction.status})
    
    # Check with M-Pesa if still pending
    if transaction.checkout_request_id:
        mpesa = MpesaGateway()
        result = mpesa.check_payment_status(transaction.checkout_request_id)
        
        if result:
            if result.get('ResultCode') == '0':
                # Payment successful
                transaction.status = 'completed'
                transaction.mpesa_receipt = result.get('MpesaReceiptNumber')
                transaction.completed_at = timezone.now()
                transaction.save()
                
                order = transaction.order
                order.payment_status = 'paid'
                order.payment_method = 'mpesa'
                order.payment_reference = transaction.reference
                order.mpesa_receipt = result.get('MpesaReceiptNumber')
                order.estimated_delivery_date = timezone.now().date() + timedelta(days=5)
                order.save()
                
                return JsonResponse({'status': 'completed'})
                
            elif result.get('ResultCode') == '1037':
                # User cancelled
                transaction.status = 'cancelled'
                transaction.save()
                return JsonResponse({'status': 'cancelled'})
                
            elif result.get('ResultCode') in ['1032', '1033', '1034', '2001']:
                # Failed (insufficient funds, etc.)
                transaction.status = 'failed'
                transaction.save()
                return JsonResponse({'status': 'failed'})
    
    return JsonResponse({'status': 'pending'})


