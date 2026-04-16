from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum, Count
from django.http import JsonResponse
from .models import UserProfile, FarmerProfile, BuyerProfile
from .forms import UserProfileForm, FarmerProfileForm, BuyerProfileForm
from marketplace.models import Produce, Order

# ========== DASHBOARD & PROFILE VIEWS ==========

@login_required
def dashboard(request):
    """Main dashboard view - shows different content based on user role"""
    profile = request.user.profile
    context = {
        'profile': profile, 
        'user': request.user,
    }
    
    if profile.role == 'farmer':
        produce_list = Produce.objects.filter(farmer=request.user, is_deleted=False)
        context['produce_list'] = produce_list
        context['total_products'] = produce_list.count()
        context['total_quantity'] = produce_list.aggregate(total=Sum('quantity'))['total'] or 0
        
        # Get orders received
        orders = Order.objects.filter(produce__farmer=request.user)
        context['total_orders'] = orders.count()
        context['pending_orders'] = orders.filter(status='pending').count()
        
    elif profile.role == 'buyer':
        orders = Order.objects.filter(buyer=request.user).order_by('-order_date')
        context['orders'] = orders
        context['total_orders'] = orders.count()
        context['total_spent'] = orders.aggregate(total=Sum('total_price'))['total'] or 0
        context['pending_orders'] = orders.filter(status='pending').count()
        context['delivered_orders'] = orders.filter(status='delivered').count()
    
    return render(request, 'accounts/dashboard.html', context)

@login_required
def my_listings(request):
    """View for farmer's product listings"""
    if request.user.profile.role != 'farmer':
        messages.error(request, 'Only farmers can access listings.')
        return redirect('dashboard')
    
    produce_list = Produce.objects.filter(farmer=request.user, is_deleted=False).order_by('-created_at')
    return render(request, 'accounts/my_listings.html', {'produce_list': produce_list})

@login_required
def my_orders(request):
    """View for buyer's orders"""
    if request.user.profile.role != 'buyer':
        messages.error(request, 'Only buyers can access orders.')
        return redirect('dashboard')
    
    orders = Order.objects.filter(buyer=request.user).order_by('-order_date')
    return render(request, 'accounts/my_orders.html', {'orders': orders})

@login_required
def received_orders(request):
    """View for farmer's received orders"""
    if request.user.profile.role != 'farmer':
        messages.error(request, 'Only farmers can access received orders.')
        return redirect('dashboard')
    
    orders = Order.objects.filter(produce__farmer=request.user).order_by('-order_date')
    return render(request, 'accounts/received_orders.html', {'orders': orders})

@login_required
def profile_view(request):
    """View user profile"""
    profile = request.user.profile
    context = {
        'profile': profile,
        'user': request.user,
    }
    
    # Add role-specific data
    if profile.role == 'farmer' and hasattr(profile, 'farmer_details'):
        context['farmer_details'] = profile.farmer_details
    elif profile.role == 'buyer' and hasattr(profile, 'buyer_details'):
        context['buyer_details'] = profile.buyer_details
    
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile(request):
    """Edit user profile"""
    profile = request.user.profile
    
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email')
        user.save()
        
        profile.phone_number = request.POST.get('phone_number', '')
        profile.location = request.POST.get('location', '')
        
        if request.FILES.get('profile_picture'):
            profile.profile_picture = request.FILES.get('profile_picture')
        
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    return render(request, 'accounts/edit_profile.html', {'profile': profile})

@login_required
def my_stats(request):
    """View user statistics"""
    profile = request.user.profile
    context = {
        'profile': profile,
        'user': request.user,
    }
    
    if profile.role == 'farmer':
        produce_list = Produce.objects.filter(farmer=request.user)
        orders = Order.objects.filter(produce__farmer=request.user, status='delivered')
        
        context['total_products'] = produce_list.count()
        context['total_value'] = produce_list.aggregate(total=Sum('price'))['total'] or 0
        context['total_revenue'] = orders.aggregate(total=Sum('total_price'))['total'] or 0
        context['total_orders'] = orders.count()
        
    elif profile.role == 'buyer':
        orders = Order.objects.filter(buyer=request.user)
        context['total_orders'] = orders.count()
        context['total_spent'] = orders.aggregate(total=Sum('total_price'))['total'] or 0
        context['active_orders'] = orders.exclude(status__in=['delivered', 'cancelled']).count()
    
    return render(request, 'accounts/stats.html', context)

# ========== ROLE REGISTRATION VIEWS ==========

@login_required
def become_farmer(request):
    """Register as a farmer"""
    if request.user.profile.role and request.user.profile.role != 'admin':
        messages.warning(request, f'You are already registered as a {request.user.profile.role}.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        profile = request.user.profile
        profile.role = 'farmer'
        profile.save()
        
        FarmerProfile.objects.create(
            user_profile=profile,
            farm_name=request.POST.get('farm_name'),
            farm_location=request.POST.get('farm_location'),
            farm_size=request.POST.get('farm_size'),
            certification=request.POST.get('certification', ''),
            registration_number=request.POST.get('registration_number', '')
        )
        
        messages.success(request, 'Successfully registered as a farmer! You can now list your produce for sale.')
        return redirect('dashboard')
    
    return render(request, 'accounts/become_farmer.html')

@login_required
def become_buyer(request):
    """Register as a buyer"""
    if request.user.profile.role and request.user.profile.role != 'admin':
        messages.warning(request, f'You are already registered as a {request.user.profile.role}.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        profile = request.user.profile
        profile.role = 'buyer'
        profile.save()
        
        BuyerProfile.objects.create(
            user_profile=profile,
            company_name=request.POST.get('company_name', ''),
            business_registration=request.POST.get('business_registration', ''),
            preferred_categories=request.POST.get('preferred_categories', '')
        )
        
        messages.success(request, 'Successfully registered as a buyer! You can now start shopping.')
        return redirect('dashboard')
    
    return render(request, 'accounts/become_buyer.html')

# ========== AJAX UTILITY VIEWS ==========

def check_username(request):
    """Check if username is available (for AJAX)"""
    username = request.GET.get('username', '')
    
    if len(username) < 3:
        return JsonResponse({
            'exists': False, 
            'valid': False,
            'message': 'Username must be at least 3 characters long'
        })
    
    if not username.replace('_', '').isalnum():
        return JsonResponse({
            'exists': False,
            'valid': False,
            'message': 'Username can only contain letters, numbers, and underscores'
        })
    
    exists = User.objects.filter(username__iexact=username).exists()
    
    return JsonResponse({
        'exists': exists,
        'valid': not exists,
        'message': 'Username already taken' if exists else 'Username available'
    })

def check_email(request):
    """Check if email is available (for AJAX)"""
    email = request.GET.get('email', '')
    
    if email:
        exists = User.objects.filter(email__iexact=email).exists()
        return JsonResponse({
            'exists': exists,
            'valid': not exists,
            'message': 'Email already registered' if exists else 'Email available'
        })
    
    return JsonResponse({'exists': False, 'valid': True, 'message': ''})

# ========== USER MANAGEMENT VIEWS ==========

@login_required
def delete_account(request):
    """Delete user account"""
    if request.method == 'POST':
        user = request.user
        user.delete()
        messages.success(request, 'Your account has been deleted successfully.')
        return redirect('home')
    
    return render(request, 'accounts/delete_account.html')

@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('change_password')
        
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('change_password')
        
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('change_password')
        
        request.user.set_password(new_password)
        request.user.save()
        
        messages.success(request, 'Password changed successfully! Please login again.')
        return redirect('account_login')
    
    return render(request, 'accounts/change_password.html')





