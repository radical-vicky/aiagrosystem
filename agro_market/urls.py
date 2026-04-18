# agro_market/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from marketplace import views as marketplace_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Home page
    path('', marketplace_views.home_view, name='home'),
    
    # Redirect /dashboard/ to /accounts/
    path('dashboard/', RedirectView.as_view(url='/accounts/', permanent=False)),
    
    # Accounts URLs
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    
    # Other apps
    path('marketplace/', include('marketplace.urls')),
    path('ai/', include('ai_predictions.urls')),
    path('transactions/', include('transactions.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)