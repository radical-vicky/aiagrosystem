from django.urls import path
from . import views

urlpatterns = [
    path('insights/', views.market_insights, name='market_insights'),
    path('api/predict/', views.predict_price_api, name='predict_price_api'),
    path('api/crops/', views.get_crops_list, name='get_crops_list'),
    path('api/history/', views.prediction_history, name='prediction_history'),
]