# accounts/admin.py (Simpler version without timezone in admin)

from django.contrib import admin
from .models import UserProfile, FarmerProfile, BuyerProfile, PhoneVerification, GovernmentID

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone_number', 'location', 'verification_level', 'phone_verified', 'id_verified', 'is_verified_farmer']
    list_filter = ['role', 'verification_level', 'phone_verified', 'id_verified', 'is_verified_farmer']
    search_fields = ['user__username', 'user__email', 'phone_number', 'location']
    readonly_fields = ['created_at', 'updated_at', 'verified_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role', 'phone_number', 'location', 'profile_picture')
        }),
        ('Verification Status', {
            'fields': ('verification_level', 'phone_verified', 'id_verified', 'is_verified_farmer', 'verified_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(FarmerProfile)
class FarmerProfileAdmin(admin.ModelAdmin):
    list_display = ['farm_name', 'user_profile', 'farm_location', 'farm_size', 'is_verified']
    list_filter = ['is_verified', 'certification']
    search_fields = ['farm_name', 'registration_number', 'user_profile__user__username']
    list_editable = ['is_verified']
    
    fieldsets = (
        ('Farm Information', {
            'fields': ('user_profile', 'farm_name', 'farm_location', 'farm_size')
        }),
        ('Certification & Registration', {
            'fields': ('certification', 'registration_number', 'is_verified')
        }),
    )

@admin.register(BuyerProfile)
class BuyerProfileAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'company_name', 'business_registration']
    search_fields = ['company_name', 'business_registration', 'user_profile__user__username']
    
    fieldsets = (
        ('Buyer Information', {
            'fields': ('user_profile', 'company_name', 'business_registration', 'preferred_categories')
        }),
    )

@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'is_verified', 'created_at', 'expires_at', 'attempts']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone_number']
    readonly_fields = ['created_at', 'expires_at', 'attempts']
    
    fieldsets = (
        ('Verification Details', {
            'fields': ('user', 'phone_number', 'otp_code', 'is_verified')
        }),
        ('Status', {
            'fields': ('attempts', 'created_at', 'expires_at')
        }),
    )

@admin.register(GovernmentID)
class GovernmentIDAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'id_type', 'id_number', 'status', 'uploaded_at']
    list_filter = ['id_type', 'status', 'uploaded_at']
    search_fields = ['user_profile__user__username', 'id_number', 'extracted_name']
    readonly_fields = ['uploaded_at', 'reviewed_at', 'extracted_name', 'extracted_dob', 'extracted_address']
    list_editable = ['status']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user_profile',)
        }),
        ('ID Details', {
            'fields': ('id_type', 'id_number', 'id_document', 'selfie_with_id')
        }),
        ('Verification Status', {
            'fields': ('status', 'rejection_reason', 'reviewed_by', 'reviewed_at')
        }),
        ('Extracted Data (Auto)', {
            'fields': ('extracted_name', 'extracted_dob', 'extracted_address'),
            'classes': ('collapse',)
        }),
    )