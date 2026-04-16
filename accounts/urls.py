from django.urls import path
from . import views

urlpatterns = [
    # Dashboard & Profile
    path('', views.dashboard, name='dashboard'),
    path('listings/', views.my_listings, name='my_listings'),
    path('orders/', views.my_orders, name='my_orders'),
    path('received-orders/', views.received_orders, name='received_orders'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),  # Add this line
    path('stats/', views.my_stats, name='my_stats'),
    path('profile/delete/', views.delete_account, name='delete_account'),
    
    # Role Registration
    path('become-farmer/', views.become_farmer, name='become_farmer'),
    path('become-buyer/', views.become_buyer, name='become_buyer'),
    
    # AJAX Endpoints
    path('check-username/', views.check_username, name='check_username'),
    path('check-email/', views.check_email, name='check_email'),
    
]