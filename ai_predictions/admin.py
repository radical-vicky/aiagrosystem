from django.contrib import admin
from .models import PricePrediction

@admin.register(PricePrediction)
class PricePredictionAdmin(admin.ModelAdmin):
    list_display = ['produce', 'predicted_price', 'confidence_score', 'demand_level', 'prediction_date']
    list_filter = ['demand_level', 'prediction_date']
    search_fields = ['produce__name']