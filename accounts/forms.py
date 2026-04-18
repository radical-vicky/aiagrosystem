# accounts/forms.py

from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, FarmerProfile, BuyerProfile, GovernmentID
from allauth.account.forms import SignupForm

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
        ('', 'Select your role'),
        ('farmer', 'Farmer - I want to sell produce'),
        ('buyer', 'Buyer - I want to buy produce'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES, 
        required=True,
        widget=forms.RadioSelect(attrs={'class': 'role-radio'})
    )
    
    # Farmer-specific fields
    farm_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Green Acres Farm'
        })
    )
    farm_location = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City, State or GPS coordinates'
        })
    )
    farm_size = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Size in acres'
        })
    )
    certification = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Organic Certified, GAP Certified'
        })
    )
    registration_number = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Farm registration number (optional)'
        })
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
        role = cleaned_data.get('role')
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        farm_name = cleaned_data.get('farm_name')
        farm_location = cleaned_data.get('farm_location')
        farm_size = cleaned_data.get('farm_size')
        
        # Validate passwords match
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        
        # Validate farmer fields if role is farmer
        if role == 'farmer':
            if not farm_name:
                self.add_error('farm_name', 'Farm name is required for farmers')
            if not farm_location:
                self.add_error('farm_location', 'Farm location is required for farmers')
            if not farm_size:
                self.add_error('farm_size', 'Farm size is required for farmers')
            elif farm_size <= 0:
                self.add_error('farm_size', 'Farm size must be greater than 0')
        
        return cleaned_data
    
    def save(self, request):
        # Save the user first
        user = super().save(request)
        
        # Get the cleaned data
        role = self.cleaned_data.get('role')
        
        # Update the user's profile with the selected role
        if role:
            user.profile.role = role
            user.profile.save()
            
            # Create role-specific profile
            if role == 'farmer':
                FarmerProfile.objects.create(
                    user_profile=user.profile,
                    farm_name=self.cleaned_data.get('farm_name'),
                    farm_location=self.cleaned_data.get('farm_location'),
                    farm_size=self.cleaned_data.get('farm_size'),
                    certification=self.cleaned_data.get('certification', ''),
                    registration_number=self.cleaned_data.get('registration_number', ''),
                    is_verified=False  # Will be verified later
                )
            elif role == 'buyer':
                BuyerProfile.objects.create(
                    user_profile=user.profile,
                    company_name=self.cleaned_data.get('company_name', ''),
                    business_registration=self.cleaned_data.get('business_registration', ''),
                    preferred_categories=self.cleaned_data.get('preferred_categories', '')
                )
        
        return user

# ========== VERIFICATION FORMS ==========

class PhoneVerificationForm(forms.Form):
    """Form for phone number input during verification"""
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., +2348012345678',
            'id': 'phone_number'
        }),
        help_text="Enter phone number with country code (e.g., +234 for Nigeria, +1 for USA, +44 for UK)"
    )
    
    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number'].strip()
        
        # Remove any spaces or dashes
        phone = phone.replace(' ', '').replace('-', '')
        
        # Basic validation
        if not phone.startswith('+'):
            raise forms.ValidationError('Please include country code (e.g., +234 for Nigeria)')
        
        if not phone[1:].isdigit():
            raise forms.ValidationError('Phone number should contain only digits after country code')
        
        # Minimum length validation (country code + at least 7 digits)
        if len(phone) < 10:
            raise forms.ValidationError('Invalid phone number length. Please enter a complete phone number.')
        
        # Maximum length validation
        if len(phone) > 15:
            raise forms.ValidationError('Phone number is too long. Maximum 15 characters including country code.')
        
        return phone

class OTPVerificationForm(forms.Form):
    """Form for OTP code input"""
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 6-digit code',
            'id': 'otp_code',
            'pattern': '[0-9]{6}',
            'title': 'Please enter 6 digits'
        })
    )
    
    def clean_otp_code(self):
        otp = self.cleaned_data['otp_code']
        if not otp.isdigit():
            raise forms.ValidationError('OTP must contain only numbers')
        return otp

class GovernmentIDForm(forms.ModelForm):
    """Form for government ID upload"""
    confirm_id_number = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm ID number'
        })
    )
    
    class Meta:
        model = GovernmentID
        fields = ['id_type', 'id_number', 'id_document', 'selfie_with_id']
        widgets = {
            'id_type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_type'
            }),
            'id_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter ID number',
                'id': 'id_number'
            }),
            'id_document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,.pdf',
                'id': 'id_document'
            }),
            'selfie_with_id': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'selfie_with_id'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add help texts
        self.fields['id_type'].help_text = "Select the type of government ID you're uploading"
        self.fields['id_number'].help_text = "Enter the ID number exactly as it appears on your document"
        self.fields['id_document'].help_text = "Upload a clear photo or scan of your ID (JPG, PNG, or PDF)"
        self.fields['selfie_with_id'].help_text = "Upload a selfie holding your ID next to your face"
    
    def clean(self):
        cleaned_data = super().clean()
        id_number = cleaned_data.get('id_number')
        confirm_id_number = cleaned_data.get('confirm_id_number')
        
        if id_number and confirm_id_number:
            # Remove spaces and convert to uppercase for comparison
            id_number_clean = id_number.replace(' ', '').upper()
            confirm_clean = confirm_id_number.replace(' ', '').upper()
            
            if id_number_clean != confirm_clean:
                raise forms.ValidationError('ID numbers do not match. Please enter the same ID number.')
        
        return cleaned_data
    
    def clean_id_document(self):
        id_doc = self.cleaned_data.get('id_document')
        if id_doc:
            # Check file size (max 5MB)
            if id_doc.size > 5 * 1024 * 1024:
                raise forms.ValidationError('File size too large. Maximum size is 5MB.')
            
            # Check file extension
            valid_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
            import os
            ext = os.path.splitext(id_doc.name)[1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError('Unsupported file type. Please upload JPG, PNG, or PDF.')
        
        return id_doc
    
    def clean_selfie_with_id(self):
        selfie = self.cleaned_data.get('selfie_with_id')
        if selfie:
            # Check file size (max 5MB)
            if selfie.size > 5 * 1024 * 1024:
                raise forms.ValidationError('File size too large. Maximum size is 5MB.')
            
            # Check file extension (only images)
            valid_extensions = ['.jpg', '.jpeg', '.png']
            import os
            ext = os.path.splitext(selfie.name)[1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError('Unsupported file type. Please upload JPG or PNG for selfie.')
        
        return selfie