from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse

class DuplicateUsernameMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        # Check if it's a duplicate username error
        if isinstance(exception, IntegrityError):
            error_msg = str(exception)
            if 'UNIQUE constraint failed: auth_user.username' in error_msg:
                messages.error(request, 'This username is already taken. Please choose a different username.')
                return HttpResponseRedirect(reverse('account_signup'))
            
            if 'UNIQUE constraint failed: auth_user.email' in error_msg:
                messages.error(request, 'This email address is already registered. Please use a different email or login.')
                return HttpResponseRedirect(reverse('account_signup'))
        
        return None
    
    
    
    
from django.shortcuts import redirect
from django.urls import reverse

class RoleCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip for certain paths
        skip_paths = [
            '/accounts/', '/admin/', '/dashboard/become-farmer/', 
            '/dashboard/become-buyer/', '/dashboard/profile/',
            '/logout/', '/login/'
        ]
        
        # Check if user is authenticated but has no role
        if request.user.is_authenticated:
            # Skip if path is in skip list
            for path in skip_paths:
                if request.path.startswith(path):
                    return None
            
            # If user has no role, redirect to dashboard
            if not request.user.profile.role and request.path != reverse('dashboard'):
                return redirect('dashboard')
        
        return None