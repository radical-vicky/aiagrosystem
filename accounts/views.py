# accounts/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum, Count
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import UserProfile, FarmerProfile, BuyerProfile, PhoneVerification, GovernmentID
from .forms import UserProfileForm, FarmerProfileForm, BuyerProfileForm, PhoneVerificationForm, OTPVerificationForm, GovernmentIDForm
from .utils import OTPService, IDVerificationService
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

# accounts/views.py

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
        return redirect('accounts:profile')  # Change this line
    
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
    """Register as a farmer with verification check"""
    
    # Check verification status
    profile = request.user.profile
    
    # If not verified, redirect to verification
    if not profile.phone_verified:
        messages.warning(request, 'Please verify your phone number before becoming a farmer.')
        return redirect('accounts:verify_phone')
    
    if not profile.id_verified:
        messages.warning(request, 'Please verify your government ID before becoming a farmer.')
        return redirect('upload_government_id')
    
    if request.user.profile.role and request.user.profile.role != 'admin':
        messages.warning(request, f'You are already registered as a {request.user.profile.role}.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        profile = request.user.profile
        profile.role = 'farmer'
        profile.is_verified_farmer = True
        profile.verification_level = 'fully_verified'
        profile.save()
        
        FarmerProfile.objects.create(
            user_profile=profile,
            farm_name=request.POST.get('farm_name'),
            farm_location=request.POST.get('farm_location'),
            farm_size=request.POST.get('farm_size'),
            certification=request.POST.get('certification', ''),
            registration_number=request.POST.get('registration_number', ''),
            is_verified=True
        )
        
        messages.success(request, 'Successfully registered as a verified farmer! You can now list your produce for sale.')
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

# ========== PHONE VERIFICATION VIEWS ==========

@login_required
def verify_phone(request):
    """Step 1: Phone number verification with OTP"""
    
    # Check if already verified
    if request.user.profile.phone_verified:
        messages.info(request, 'Your phone is already verified.')
        return redirect('accounts:verification_status')
    
    if request.method == 'POST':
        form = PhoneVerificationForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data['phone_number']
            
            # Check if phone already used by another user
            if PhoneVerification.objects.filter(phone_number=phone_number, is_verified=True).exclude(user=request.user).exists():
                messages.error(request, 'This phone number is already verified by another user.')
                return redirect('accounts:verify_phone')
            
            # Generate OTP
            otp_code = OTPService.generate_otp()
            
            # Save or update verification record
            verification, created = PhoneVerification.objects.update_or_create(
                user=request.user,
                defaults={
                    'phone_number': phone_number,
                    'otp_code': otp_code,
                    'expires_at': timezone.now() + timedelta(minutes=10),
                    'attempts': 0,
                    'is_verified': False
                }
            )
            
            # Send OTP via SMS
            success = OTPService.send_otp_via_sms(phone_number, otp_code)
            
            if success:
                messages.success(request, f'OTP sent to {phone_number}. Valid for 10 minutes.')
                request.session['verification_phone'] = phone_number
                return redirect('accounts:verify_otp')  # FIXED: Added accounts: namespace
            else:
                messages.error(request, 'Failed to send OTP. Please try again.')
    
    else:
        form = PhoneVerificationForm()
    
    return render(request, 'accounts/verify_phone.html', {'form': form})

@login_required
def verify_otp(request):
    """Step 2: Verify OTP code"""
    
    phone_number = request.session.get('verification_phone')
    if not phone_number:
        messages.error(request, 'Please request OTP first.')
        return redirect('accounts:verify_phone')
    
    verification = get_object_or_404(PhoneVerification, user=request.user, phone_number=phone_number)
    
    if verification.is_verified:
        messages.info(request, 'Phone already verified.')
        return redirect('accounts:verification_status')

    
    if verification.is_expired():
        messages.error(request, 'OTP has expired. Please request a new one.')
        verification.delete()
        return redirect('accounts:verify_phone')
    
    if verification.attempts >= 5:
        messages.error(request, 'Too many failed attempts. Please request a new OTP.')
        verification.delete()
        return redirect('accounts:verify_phone')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']
            
            if verification.otp_code == otp_code:
                # Mark as verified
                verification.is_verified = True
                verification.save()
                
                # Update user profile
                profile = request.user.profile
                profile.phone_verified = True
                profile.verification_level = 'phone_verified'
                profile.save()
                
                messages.success(request, 'Phone number verified successfully!')
                
                # Clean up session
                del request.session['verification_phone']
                
                return redirect('accounts:verification_status')

            else:
                verification.attempts += 1
                verification.save()
                messages.error(request, f'Invalid OTP. {5 - verification.attempts} attempts remaining.')
    
    else:
        form = OTPVerificationForm()
    
    return render(request, 'accounts/verify_otp.html', {
        'form': form,
        'phone_number': phone_number
    })

@login_required
def resend_otp(request):
    """Resend OTP code"""
    
    phone_number = request.session.get('verification_phone')
    if not phone_number:
        messages.error(request, 'Please request OTP first.')
        return redirect('accounts:verify_phone')
    
    verification = PhoneVerification.objects.filter(user=request.user, phone_number=phone_number).first()
    
    if verification and not verification.is_verified:
        # Generate new OTP
        new_otp = OTPService.generate_otp()
        verification.otp_code = new_otp
        verification.expires_at = timezone.now() + timedelta(minutes=10)
        verification.attempts = 0
        verification.save()
        
        # Resend SMS
        success = OTPService.send_otp_via_sms(phone_number, new_otp)
        
        if success:
            messages.success(request, f'New OTP sent to {phone_number}')
        else:
            messages.error(request, 'Failed to send OTP. Please try again.')
    
    return redirect('accounts:verify_otp')  # FIXED: Added accounts: namespace
# ========== ID VERIFICATION VIEWS ==========

@login_required
def upload_government_id(request):
    """Step 3: Upload government ID for verification"""
    
    # Check if phone is verified first
    if not request.user.profile.phone_verified:
        messages.warning(request, 'Please verify your phone number first.')
        return redirect('accounts:verify_phone')
    
    # Check if already uploaded
    if hasattr(request.user.profile, 'government_id'):
        if request.user.profile.government_id.status == 'approved':
            messages.info(request, 'Your ID is already verified.')
            return redirect('accounts:verification_status')
        elif request.user.profile.government_id.status == 'pending':
            messages.info(request, 'Your ID is pending review. Please wait.')
            return redirect('accounts:verification_status')
    
    if request.method == 'POST':
        form = GovernmentIDForm(request.POST, request.FILES)
        if form.is_valid():
            # Validate ID format
            id_number = form.cleaned_data['id_number']
            id_type = form.cleaned_data['id_type']
            
            if not IDVerificationService.validate_id_format(id_number, id_type):
                messages.error(request, f'Invalid {dict(GovernmentID.ID_TYPES).get(id_type)} number format.')
                return redirect('accounts:upload_government_id')  # FIXED: Added accounts: namespace
            
            # Save ID document
            government_id = form.save(commit=False)
            government_id.user_profile = request.user.profile
            government_id.save()
            
            # Auto-approve for now (you can add API verification later)
            government_id.status = 'approved'
            government_id.save()
            
            # Update profile
            profile = request.user.profile
            profile.id_verified = True
            profile.verification_level = 'id_verified'
            profile.save()
            
            messages.success(request, 'Government ID verified successfully! You can now become a verified farmer.')
            return redirect('accounts:verification_status')  # FIXED: Added accounts: namespace
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = GovernmentIDForm()
    
    return render(request, 'accounts/upload_id.html', {'form': form})


@login_required
def verification_status(request):
    """Show verification status dashboard"""
    
    profile = request.user.profile
    
    # Get verification details
    phone_verification = PhoneVerification.objects.filter(user=request.user).first()
    id_verification = GovernmentID.objects.filter(user_profile=profile).first()
    
    context = {
        'profile': profile,
        'phone_verification': phone_verification,
        'id_verification': id_verification,
        'verification_levels': {
            'email': True,  # Assume email is verified through registration
            'phone': profile.phone_verified,
            'id': profile.id_verified,
        }
    }
    
    return render(request, 'accounts/verification_status.html', context)

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