from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, FarmerProfile, BuyerProfile
from allauth.account.forms import SignupForm
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'location', 'profile_picture']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

class FarmerProfileForm(forms.ModelForm):
    class Meta:
        model = FarmerProfile
        fields = ['farm_name', 'farm_location', 'farm_size', 'certification', 'registration_number']
        widgets = {
            'farm_size': forms.NumberInput(attrs={'step': '0.01'}),
        }

class BuyerProfileForm(forms.ModelForm):
    class Meta:
        model = BuyerProfile
        fields = ['company_name', 'business_registration', 'preferred_categories']
        widgets = {
            'preferred_categories': forms.Textarea(attrs={'rows': 3}),
        }
        
        


class CustomSignupForm(SignupForm):
    ROLE_CHOICES = [
        ('', 'Select your role'),  # Empty choice as default
        ('farmer', 'Farmer - I want to sell produce'),
        ('buyer', 'Buyer - I want to buy produce'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES, 
        required=True,
        widget=forms.Select(attrs={'class': 'form-control form-control-lg'})
    )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken. Please choose another username.')
        if len(username) < 3:
            raise forms.ValidationError('Username must be at least 3 characters long.')
        if not username.replace('_', '').isalnum():
            raise forms.ValidationError('Username can only contain letters, numbers, and underscores.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email address is already registered. Please use a different email or login.')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        
        return cleaned_data
    
    def save(self, request):
        # Save the user first
        user = super().save(request)
        
        # Get the selected role
        role = self.cleaned_data.get('role')
        
        # Update the user's profile with the selected role
        if role:
            user.profile.role = role
            user.profile.save()
            
            # If role is farmer, create empty farmer profile (will be filled later)
            if role == 'farmer':
                from .models import FarmerProfile
                FarmerProfile.objects.get_or_create(
                    user_profile=user.profile,
                    defaults={
                        'farm_name': 'My Farm',
                        'farm_location': user.profile.location or 'Not specified',
                        'farm_size': 0
                    }
                )
            
            # If role is buyer, create empty buyer profile
            elif role == 'buyer':
                from .models import BuyerProfile
                BuyerProfile.objects.get_or_create(
                    user_profile=user.profile,
                    defaults={
                        'company_name': '',
                        'business_registration': '',
                        'preferred_categories': ''
                    }
                )
        
        return user