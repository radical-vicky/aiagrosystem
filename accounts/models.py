# accounts/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
import os

def government_id_upload_path(instance, filename):
    """Generate unique path for government ID uploads"""
    ext = filename.split('.')[-1]
    filename = f"{instance.user_profile.user.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    return os.path.join('government_ids', filename)

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
        ('admin', 'Administrator'),
    ]
    
    VERIFICATION_LEVELS = [
        ('unverified', 'Unverified'),
        ('email_verified', 'Email Verified'),
        ('phone_verified', 'Phone Verified'),
        ('id_verified', 'ID Verified'),
        ('fully_verified', 'Fully Verified')
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')
    phone_number = models.CharField(max_length=15, blank=True)
    location = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    
    # New verification fields
    verification_level = models.CharField(max_length=20, choices=VERIFICATION_LEVELS, default='unverified')
    phone_verified = models.BooleanField(default=False)
    id_verified = models.BooleanField(default=False)
    is_verified_farmer = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    class Meta:
        verbose_name_plural = 'User Profiles'

class FarmerProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='farmer_details')
    farm_name = models.CharField(max_length=100)
    farm_location = models.CharField(max_length=200)
    farm_size = models.DecimalField(max_digits=10, decimal_places=2, help_text="Size in acres")
    certification = models.CharField(max_length=100, blank=True)
    registration_number = models.CharField(max_length=50, blank=True)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return self.farm_name

class BuyerProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='buyer_details')
    company_name = models.CharField(max_length=100, blank=True)
    business_registration = models.CharField(max_length=50, blank=True)
    preferred_categories = models.TextField(blank=True, help_text="Comma-separated categories")
    
    def __str__(self):
        return self.company_name or self.user_profile.user.username

class PhoneVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='phone_verification')
    phone_number = models.CharField(max_length=15)
    otp_code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"{self.user.username} - {self.phone_number}"

class GovernmentID(models.Model):
    ID_TYPES = [
        ('national_id', 'National ID Card'),
        ('drivers_license', "Driver's License"),
        ('passport', 'International Passport'),
        ('voter_id', "Voter's Card"),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='government_id')
    id_type = models.CharField(max_length=20, choices=ID_TYPES)
    id_number = models.CharField(max_length=50)
    id_document = models.FileField(upload_to=government_id_upload_path)
    selfie_with_id = models.ImageField(upload_to='selfie_ids/')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True, null=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Store extracted data for verification
    extracted_name = models.CharField(max_length=100, blank=True)
    extracted_dob = models.DateField(null=True, blank=True)
    extracted_address = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user_profile.user.username} - {self.get_id_type_display()}"

# Signal receivers for creating/updating UserProfile
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()