from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from marketplace.models import Order
from .models import Payment
from .mpesa import mpesa_api
import json

@login_required
def initiate_payment(request, order_id):
    """Initiate payment for order"""
    order = get_object_or_404(Order, id=order_id, buyer=request.user)
    
    # Check if payment already exists for this order
    existing_payment = Payment.objects.filter(order=order).first()
    
    if existing_payment:
        if existing_payment.status == 'completed':
            messages.warning(request, 'Payment has already been completed for this order.')
            return redirect('order_detail', pk=order.id)
        elif existing_payment.status == 'pending':
            # Instead of redirecting, allow retry with a new payment
            messages.info(request, 'Previous payment attempt failed or expired. Please try again.')
            # Delete the old pending payment to allow new attempt
            existing_payment.delete()
        else:
            # Delete failed payment to allow retry
            existing_payment.delete()
            messages.info(request, 'Previous payment attempt failed. Please try again.')
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        phone_number = request.POST.get('phone_number', '')
        
        if payment_method == 'cash':
            # Create payment record
            payment = Payment.objects.create(
                order=order,
                amount=order.total_price,
                payment_method='cash',
                status='completed'
            )
            # Update order status
            order.status = 'confirmed'
            order.save()
            messages.success(request, f'Order confirmed with Cash on Delivery! Payment ID: {payment.transaction_id}')
            return redirect('order_detail', pk=order.id)
            
        elif payment_method == 'mpesa':
            if not phone_number:
                messages.error(request, 'Phone number is required for M-Pesa payment.')
                return redirect('initiate_payment', order_id=order.id)
            
            # Format phone number (remove 0 or +254, add 254)
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif phone_number.startswith('+'):
                phone_number = phone_number[1:]
            
            # Create payment record
            payment = Payment.objects.create(
                order=order,
                amount=order.total_price,
                payment_method='mpesa',
                phone_number=phone_number,
                status='pending'
            )
            
            # Initiate M-Pesa STK Push
            response = mpesa_api.stk_push(
                phone_number=phone_number,
                amount=float(order.total_price),
                account_reference=order.order_number,
                transaction_desc=f"Payment for order {order.order_number}"
            )
            
            if response and response.get('ResponseCode') == '0':
                messages.success(request, f'M-Pesa STK Push sent to {phone_number}! Please check your phone and enter your PIN to complete payment.')
                return redirect('payment_status', payment_id=payment.id)
            else:
                # Update payment as failed
                payment.status = 'failed'
                payment.save()
                error_msg = response.get('ResponseDescription', 'Failed to initiate M-Pesa payment') if response else 'M-Pesa service unavailable'
                messages.error(request, f'{error_msg}. Please try again or use Cash on Delivery.')
                return redirect('initiate_payment', order_id=order.id)
    
    return render(request, 'transactions/initiate_payment.html', {'order': order})

@login_required
def payment_status(request, payment_id):
    """Payment status view with auto-refresh"""
    payment = get_object_or_404(Payment, id=payment_id, order__buyer=request.user)
    return render(request, 'transactions/payment_status.html', {'payment': payment})

@csrf_exempt
def mpesa_callback(request):
    """M-Pesa callback handler"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(f"M-Pesa Callback received: {json.dumps(data, indent=2)}")
            
            # Extract callback data
            body = data.get('Body', {})
            stk_callback = body.get('stkCallback', {})
            result_code = stk_callback.get('ResultCode')
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            
            # Find payment by transaction_id (you need to store CheckoutRequestID)
            # For now, we'll update based on the most recent pending payment
            payment = Payment.objects.filter(status='pending').order_by('-created_at').first()
            
            if payment:
                if result_code == 0:  # Success
                    payment.status = 'completed'
                    # Get receipt number
                    callback_metadata = stk_callback.get('CallbackMetadata', {})
                    items = callback_metadata.get('Item', [])
                    for item in items:
                        if item.get('Name') == 'MpesaReceiptNumber':
                            payment.mpesa_receipt_number = item.get('Value')
                            break
                    payment.save()
                    
                    # Update order status
                    payment.order.status = 'confirmed'
                    payment.order.save()
                    
                    print(f"Payment completed for order {payment.order.order_number}")
                else:
                    payment.status = 'failed'
                    payment.save()
                    print(f"Payment failed for order {payment.order.order_number}: {stk_callback.get('ResultDesc')}")
            
            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})
        except Exception as e:
            print(f"Error processing M-Pesa callback: {e}")
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Failed'})
    
    return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Failed'})



@login_required
def cancel_payment(request, payment_id):
    """Cancel a pending payment"""
    payment = get_object_or_404(Payment, id=payment_id, order__buyer=request.user)
    
    # Only allow cancellation if payment is pending
    if payment.status == 'pending':
        payment.status = 'cancelled'
        payment.save()
        
        # Restore the order (change status back to pending)
        order = payment.order
        order.status = 'pending'
        order.save()
        
        messages.success(request, f'Payment for order {order.order_number} has been cancelled.')
        
        # Check if AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Payment cancelled successfully'})
        
        return redirect('order_detail', pk=order.id)
    else:
        messages.error(request, 'This payment cannot be cancelled.')
        return redirect('payment_status', payment_id=payment_id)
    
    
    
from django.utils import timezone
from datetime import timedelta

def check_expired_payments(request):
    """Check and cancel expired pending payments (called via AJAX or middleware)"""
    # Cancel payments older than 5 minutes that are still pending
    expiry_time = timezone.now() - timedelta(minutes=5)
    expired_payments = Payment.objects.filter(
        status='pending',
        created_at__lt=expiry_time
    )
    
    cancelled_count = 0
    for payment in expired_payments:
        payment.status = 'cancelled'
        payment.save()
        # Restore order status
        payment.order.status = 'pending'
        payment.order.save()
        cancelled_count += 1
    
    return cancelled_count