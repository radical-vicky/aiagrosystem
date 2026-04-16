from django.db import models
from marketplace.models import Produce

class PricePrediction(models.Model):
    DEMAND_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    produce = models.ForeignKey(Produce, on_delete=models.CASCADE, related_name='predictions', null=True, blank=True)
    predicted_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2)
    demand_level = models.CharField(max_length=10, choices=DEMAND_LEVELS)
    prediction_date = models.DateField(auto_now_add=True)
    factors_considered = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-prediction_date']
    
    def __str__(self):
        return f"Prediction for {self.produce.name if self.produce else 'General'}: KES {self.predicted_price}"


class MarketTrend(models.Model):
    TREND_TYPES = [
        ('price_trend', 'Price Trend'),
        ('demand_forecast', 'Demand Forecast'),
        ('seasonal', 'Seasonal Pattern'),
        ('market_alert', 'Market Alert'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    trend_type = models.CharField(max_length=20, choices=TREND_TYPES)
    category = models.ForeignKey('marketplace.Category', on_delete=models.SET_NULL, null=True, blank=True)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

class MarketInsight(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    insight_type = models.CharField(max_length=50)  # tip, alert, opportunity, warning
    priority = models.CharField(max_length=20, default='normal')  # high, medium, low
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.title