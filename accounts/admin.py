from django.contrib import admin
from .models import UserProfile, FarmerProfile, BuyerProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone_number', 'location', 'is_verified']
    list_filter = ['role', 'is_verified']
    search_fields = ['user__username', 'user__email', 'phone_number']

@admin.register(FarmerProfile)
class FarmerProfileAdmin(admin.ModelAdmin):
    list_display = ['farm_name', 'user_profile', 'farm_location', 'farm_size']
    search_fields = ['farm_name', 'registration_number']

@admin.register(BuyerProfile)
class BuyerProfileAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'company_name', 'business_registration']
    search_fields = ['company_name', 'business_registration']