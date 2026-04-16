from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from .models import Category, Produce, Order
from .forms import ProduceForm


def home_view(request):
    """Dynamic home page with real data from database"""
    
    # Get statistics from database
    total_farmers = User.objects.filter(profile__role='farmer').count()
    total_products = Produce.objects.filter(is_deleted=False, status='available').count()
    
    # Calculate satisfaction rate based on completed orders
    total_orders = Order.objects.count()
    completed_orders = Order.objects.filter(status='delivered').count()
    satisfaction_rate = int((completed_orders / total_orders * 100)) if total_orders > 0 else 98
    
    # Get featured products (latest 6 available products)
    featured_products = Produce.objects.filter(
        is_deleted=False,
        status='available'
    ).order_by('-created_at')[:6]
    
    # Calculate price trends for each product
    for product in featured_products:
        # Get average price for similar products in same category
        avg_price = Produce.objects.filter(
            category=product.category,
            is_deleted=False
        ).exclude(id=product.id).aggregate(avg=Avg('price'))['avg']
        
        if avg_price:
            if product.price > avg_price:
                product.price_trend = 'up'
                product.trend_percentage = round(((product.price - avg_price) / avg_price) * 100, 1)
            else:
                product.price_trend = 'down'
                product.trend_percentage = round(((avg_price - product.price) / avg_price) * 100, 1)
        else:
            product.price_trend = 'up'
            product.trend_percentage = 0
    
    # Format total products display
    if total_products > 1000:
        formatted_total_products = f"{total_products/1000:.1f}K"
    else:
        formatted_total_products = str(total_products)
    
    context = {
        'total_farmers': total_farmers,
        'total_products': formatted_total_products,
        'satisfaction_rate': satisfaction_rate,
        'featured_products': featured_products,
    }
    
    return render(request, 'home.html', context)


def marketplace_home(request):
    """Marketplace home page - shows all available products"""
    categories = Category.objects.all()
    
    # Get all products that are not deleted
    produce_list = Produce.objects.filter(
        is_deleted=False
    ).order_by('-created_at')
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        produce_list = produce_list.filter(category_id=category_id)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        produce_list = produce_list.filter(name__icontains=search_query)
    
    context = {
        'categories': categories,
        'produce_list': produce_list,
    }
    return render(request, 'marketplace/marketplace_home.html', context)


def produce_detail(request, pk):
    """Produce detail view"""
    produce = get_object_or_404(Produce, pk=pk, is_deleted=False)
    
    can_purchase = produce.status in ['available', 'low_stock'] and produce.quantity > 0
    
    related_products = Produce.objects.filter(
        category=produce.category, 
        status__in=['available', 'low_stock'],
        is_deleted=False
    ).exclude(pk=pk)[:4]
    
    context = {
        'produce': produce,
        'related_products': related_products,
        'can_purchase': can_purchase,
    }
    return render(request, 'marketplace/produce_detail.html', context)


@login_required
def add_produce(request):
    """Add new produce"""
    if request.user.profile.role != 'farmer':
        messages.error(request, 'Only farmers can add produce.')
        return redirect('marketplace')
    
    if request.method == 'POST':
        form = ProduceForm(request.POST, request.FILES)
        if form.is_valid():
            produce = form.save(commit=False)
            produce.farmer = request.user
            produce.save()
            messages.success(request, f'{produce.name} has been added successfully!')
            return redirect('produce_detail', pk=produce.pk)
    else:
        form = ProduceForm()
    
    return render(request, 'marketplace/add_produce.html', {'form': form})


@login_required
def edit_produce(request, pk):
    """Edit produce"""
    produce = get_object_or_404(Produce, pk=pk, is_deleted=False)
    
    if produce.farmer != request.user:
        messages.error(request, 'You do not have permission to edit this product.')
        return redirect('produce_detail', pk=pk)
    
    if request.method == 'POST':
        form = ProduceForm(request.POST, request.FILES, instance=produce)
        if form.is_valid():
            produce = form.save()
            messages.success(request, f'{produce.name} has been updated successfully!')
            return redirect('produce_detail', pk=produce.pk)
    else:
        form = ProduceForm(instance=produce)
    
    return render(request, 'marketplace/edit_produce.html', {'form': form, 'produce': produce})


@login_required
@require_http_methods(["POST"])
def delete_produce(request, pk):
    """Soft delete produce"""
    produce = get_object_or_404(Produce, pk=pk)
    
    if produce.farmer != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    produce.is_deleted = True
    produce.status = 'discontinued'
    produce.save()
    
    messages.success(request, f'{produce.name} has been removed from your listings.')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Product deleted successfully'})
    
    return redirect('dashboard')


def products_by_category(request, category_id):
    """API endpoint to get products by category with images"""
    products = Produce.objects.filter(
        category_id=category_id, 
        is_deleted=False,
        status='available'
    )
    
    product_list = []
    for product in products[:10]:
        product_list.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'image_url': product.image.url if product.image else None,
            'video_url': product.video_url,
            'quantity': float(product.quantity),
            'unit': product.unit
        })
    
    return JsonResponse({
        'products': product_list
    })


def get_featured_products(request):
    """API endpoint to get featured products with images"""
    products = Produce.objects.filter(
        is_deleted=False,
        status='available'
    ).order_by('-created_at')[:8]
    
    product_list = []
    for product in products:
        product_list.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'unit': product.unit,
            'image_url': product.image.url if product.image else None,
            'video_url': product.video_url,
            'quantity': float(product.quantity),
            'location': product.location
        })
    
    return JsonResponse({'products': product_list})


@login_required
def place_order(request, pk):
    """Place order for produce - only buyers can place orders"""
    produce = get_object_or_404(Produce, pk=pk)
    
    if request.user.profile.role != 'buyer':
        messages.error(request, 'Only buyers can place orders.')
        return redirect('produce_detail', pk=pk)
    
    if request.method == 'POST':
        from decimal import Decimal
        
        quantity = Decimal(request.POST.get('quantity'))
        delivery_address = request.POST.get('delivery_address')
        notes = request.POST.get('notes', '')
        
        if quantity > produce.quantity:
            messages.error(request, f'Insufficient quantity available! Only {produce.quantity} {produce.unit} available.')
            return redirect('produce_detail', pk=produce.pk)
        
        order = Order.objects.create(
            buyer=request.user,
            produce=produce,
            quantity=quantity,
            delivery_address=delivery_address,
            notes=notes
        )
        
        # Update produce quantity
        produce.quantity -= quantity
        if produce.quantity <= 0:
            produce.status = 'sold_out'
        produce.save()
        
        messages.success(request, f'Order {order.order_number} placed successfully!')
        return redirect('order_detail', pk=order.pk)
    
    return render(request, 'marketplace/place_order.html', {'produce': produce})


@login_required
def order_detail(request, pk):
    """Order detail view - buyers see their orders, farmers see orders for their products"""
    try:
        # Check if user is buyer of this order
        order_as_buyer = Order.objects.filter(pk=pk, buyer=request.user).first()
        
        # Check if user is farmer who owns the product in this order
        order_as_farmer = Order.objects.filter(pk=pk, produce__farmer=request.user).first()
        
        if order_as_buyer:
            # User is the buyer
            return render(request, 'marketplace/order_detail.html', {
                'order': order_as_buyer,
                'user_role': 'buyer'
            })
        elif order_as_farmer:
            # User is the farmer who owns the product
            return render(request, 'marketplace/order_detail.html', {
                'order': order_as_farmer,
                'user_role': 'farmer'
            })
        else:
            messages.error(request, 'Order not found or you do not have permission to view it.')
            return redirect('dashboard')
            
    except Exception as e:
        messages.error(request, f'Error loading order: {str(e)}')
        return redirect('dashboard')


@login_required
def cancel_order(request, pk):
    """Cancel order - only the buyer can cancel their own order"""
    try:
        order = Order.objects.filter(pk=pk, buyer=request.user).first()
        
        if not order:
            messages.error(request, 'Order not found or you do not have permission to cancel it.')
            return redirect('dashboard')
        
        if order.status == 'pending':
            order.status = 'cancelled'
            order.save()
            
            # Restore produce quantity
            produce = order.produce
            produce.quantity += order.quantity
            if produce.status == 'sold_out':
                produce.status = 'available'
            produce.save()
            
            messages.success(request, f'Order {order.order_number} cancelled successfully!')
        else:
            messages.error(request, 'This order cannot be cancelled.')
    except Exception as e:
        messages.error(request, f'Error cancelling order: {str(e)}')
    
    return redirect('dashboard')