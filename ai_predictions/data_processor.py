from django.db.models import Avg, Sum, Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from marketplace.models import Produce, Order, Category
from .models import PricePrediction, MarketTrend, MarketInsight
import random

class MarketDataProcessor:
    
    @staticmethod
    def get_price_trends():
        """Get real-time price trends for all products"""
        trends = []
        products = Produce.objects.filter(is_deleted=False, status='available')
        
        for product in products:
            # Get last 10 orders for this product
            orders = Order.objects.filter(
                produce=product,
                status='delivered'
            ).order_by('-order_date')[:10]
            
            if orders.count() >= 3:
                # Calculate average price from last orders
                avg_price = sum(float(o.total_price / o.quantity) for o in orders) / orders.count()
                
                # Calculate trend
                recent_orders = orders[:5]
                older_orders = orders[5:]
                
                if recent_orders and older_orders:
                    recent_avg = sum(float(o.total_price / o.quantity) for o in recent_orders) / len(recent_orders)
                    older_avg = sum(float(o.total_price / o.quantity) for o in older_orders) / len(older_orders)
                    
                    percentage_change = ((recent_avg - older_avg) / older_avg) * 100
                    
                    if percentage_change > 5:
                        trend = 'up'
                    elif percentage_change < -5:
                        trend = 'down'
                    else:
                        trend = 'stable'
                else:
                    trend = 'stable'
            else:
                avg_price = float(product.price)
                trend = 'stable'
            
            trends.append({
                'product': product,
                'current_price': float(product.price),
                'average_price': round(avg_price, 2),
                'trend': trend,
                'orders_count': orders.count()
            })
        
        return trends
    
    @staticmethod
    def get_demand_forecast():
        """Forecast demand based on order history"""
        forecasts = []
        categories = Category.objects.all()
        
        for category in categories:
            # Initialize variables with default values
            demand = 'unknown'
            growth = 0
            order_count = 0
            avg_order_size = 0
            total_quantity = 0
            
            # Get orders in last 30 days for this category
            thirty_days_ago = timezone.now() - timedelta(days=30)
            orders = Order.objects.filter(
                produce__category=category,
                status='delivered',
                order_date__gte=thirty_days_ago
            )
            
            if orders.exists():
                total_quantity = orders.aggregate(total=Sum('quantity'))['total'] or 0
                order_count = orders.count()
                avg_order_size = float(total_quantity / order_count) if order_count > 0 else 0
                
                # Calculate demand level
                if order_count > 50:
                    demand = 'high'
                elif order_count > 20:
                    demand = 'medium'
                else:
                    demand = 'low'
                
                # Calculate growth compared to previous period
                older_orders = Order.objects.filter(
                    produce__category=category,
                    status='delivered',
                    order_date__lt=thirty_days_ago,
                    order_date__gte=thirty_days_ago - timedelta(days=30)
                ).count()
                
                if older_orders > 0:
                    growth = ((order_count - older_orders) / older_orders) * 100
                elif order_count > 0:
                    growth = 100  # New category with orders
                else:
                    growth = 0
            
            forecasts.append({
                'category': category,
                'demand': demand,
                'growth': round(growth, 1),
                'order_count': order_count,
                'avg_order_size': round(avg_order_size, 1)
            })
        
        return forecasts
    
    @staticmethod
    def get_seasonal_patterns():
        """Analyze seasonal patterns based on historical data"""
        patterns = []
        current_month = datetime.now().month
        
        # Seasonal price patterns for different products
        seasonal_products = [
            {'name': 'Tomatoes', 'peak_months': [1, 2, 12], 'off_peak_months': [6, 7, 8]},
            {'name': 'Potatoes', 'peak_months': [7, 8, 9], 'off_peak_months': [1, 2, 3]},
            {'name': 'Onions', 'peak_months': [3, 4, 5], 'off_peak_months': [9, 10, 11]},
            {'name': 'Maize', 'peak_months': [9, 10, 11], 'off_peak_months': [3, 4, 5]},
            {'name': 'Beans', 'peak_months': [10, 11, 12], 'off_peak_months': [4, 5, 6]},
            {'name': 'Cabbage', 'peak_months': [6, 7, 8], 'off_peak_months': [12, 1, 2]},
            {'name': 'Carrots', 'peak_months': [4, 5, 6], 'off_peak_months': [10, 11, 12]},
            {'name': 'Kale', 'peak_months': [3, 4, 9, 10], 'off_peak_months': [6, 7, 12, 1]},
        ]
        
        for product_info in seasonal_products:
            if current_month in product_info['peak_months']:
                recommendation = 'peak - Good time to sell'
                price_trend = 'high'
            elif current_month in product_info['off_peak_months']:
                recommendation = 'off-peak - Good time to buy'
                price_trend = 'low'
            else:
                recommendation = 'normal season - Stable prices'
                price_trend = 'medium'
            
            patterns.append({
                'product': product_info['name'],
                'current_month': current_month,
                'recommendation': recommendation,
                'price_trend': price_trend
            })
        
        return patterns

    @staticmethod
    def get_market_alerts():
        """Generate real-time market alerts"""
        alerts = []
        
        # Check for low stock products
        low_stock = Produce.objects.filter(quantity__lt=50, status='available', is_deleted=False)
        for product in low_stock[:5]:
            alerts.append({
                'type': 'warning',
                'title': f'Low Stock Alert: {product.name}',
                'message': f'Only {product.quantity} {product.unit} remaining! Consider restocking soon.',
                'priority': 'high'
            })
        
        # Check for products with high demand (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        high_demand = Order.objects.filter(
            status='delivered',
            order_date__gte=thirty_days_ago
        ).values('produce__name').annotate(
            total=Sum('quantity')
        ).order_by('-total')[:5]
        
        for item in high_demand:
            if item['total']:
                alerts.append({
                    'type': 'info',
                    'title': f'High Demand: {item["produce__name"]}',
                    'message': f'High demand detected. {item["total"]} units sold in last 30 days.',
                    'priority': 'medium'
                })
        
        # Check for price increases
        products_with_high_demand = Produce.objects.filter(
            is_deleted=False,
            status='available'
        ).order_by('-price')[:3]
        
        for product in products_with_high_demand:
            alerts.append({
                'type': 'success',
                'title': f'Premium Product: {product.name}',
                'message': f'Currently priced at KES {product.price}/{product.unit}. High quality produce.',
                'priority': 'low'
            })
        
        return alerts

class PricePredictor:
    @staticmethod
    def predict_price(produce):
        """Simple price prediction based on historical data and seasonality"""
        from decimal import Decimal
        
        # Get historical orders
        orders = Order.objects.filter(
            produce=produce,
            status='delivered'
        ).order_by('-order_date')[:20]
        
        if orders.count() >= 5:
            # Calculate average price from historical orders
            total = sum(float(o.total_price / o.quantity) for o in orders)
            avg_price = total / orders.count()
            
            # Adjust for seasonality
            current_month = datetime.now().month
            if current_month in [1, 2, 12]:  # Peak season for some products
                seasonal_factor = 1.1
            elif current_month in [6, 7, 8]:  # Off-peak
                seasonal_factor = 0.9
            else:
                seasonal_factor = 1.0
            
            predicted = avg_price * seasonal_factor
            
            # Add random variation (for demo)
            variation = random.uniform(0.95, 1.05)
            predicted *= variation
            
            # Calculate confidence based on data points
            confidence = min(95, 50 + orders.count())
            
            # Determine demand level
            if predicted > float(produce.price) * 1.1:
                demand = 'high'
            elif predicted < float(produce.price) * 0.9:
                demand = 'low'
            else:
                demand = 'medium'
            
            return {
                'predicted_price': round(Decimal(str(predicted)), 2),
                'confidence_score': confidence,
                'demand_level': demand,
                'data_points': orders.count()
            }
        else:
            # Not enough data, use simple prediction
            return {
                'predicted_price': produce.price,
                'confidence_score': 50,
                'demand_level': 'medium',
                'data_points': orders.count()
            }