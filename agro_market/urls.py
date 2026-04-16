from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from marketplace.views import home_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),  # This handles all auth URLs including password reset
    path('dashboard/', include('accounts.urls')),
    path('marketplace/', include('marketplace.urls')),
    path('ai/', include('ai_predictions.urls')),
    path('transactions/', include('transactions.urls')),
    path('', home_view, name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)