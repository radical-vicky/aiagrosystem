from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime, timedelta
from marketplace.models import Category, Produce
from .models import PricePrediction
from .ai_service import ai_service
import json

@login_required
def market_insights(request):
    """AI predictions page with crop selection"""
    categories = Category.objects.all()
    
    # Get recent predictions
    recent_predictions = PricePrediction.objects.select_related('produce').filter(
        is_active=True
    ).order_by('-prediction_date')[:10]
    
    popular_crops = ['Maize', 'Tomatoes', 'Potatoes', 'Onions', 'Kale', 'Beans', 'Avocado', 'Carrots']
    
    # Check if Groq is configured
    from django.conf import settings
    groq_configured = bool(getattr(settings, 'GROQ_API_KEY', None))
    
    context = {
        'categories': categories,
        'recent_predictions': recent_predictions,
        'popular_crops': popular_crops,
        'current_year': datetime.now().year,
        'current_month': datetime.now().strftime('%B'),
        'groq_configured': groq_configured,
    }
    
    return render(request, 'ai_predictions/insights.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def predict_price_api(request):
    """API endpoint for AI price prediction with product images"""
    try:
        data = json.loads(request.body)
        crop_type = data.get('crop_type', 'maize')
        location = data.get('location', 'Kisumu County')
        
        # Get prediction from AI service
        result = ai_service.predict_price(crop_type, location)
        
        # Find matching product to get image
        product = Produce.objects.filter(
            name__icontains=crop_type,
            is_deleted=False
        ).first()
        
        product_data = {}
        if product:
            product_data = {
                'product_id': product.id,
                'product_name': product.name,
                'product_image': product.image.url if product.image else None,
                'product_video': product.video_url,
                'product_price': float(product.price),
                'product_quantity': float(product.quantity),
                'product_unit': product.unit,
                'product_location': product.location
            }
        
        if result.get('success'):
            # Save to database
            try:
                PricePrediction.objects.create(
                    produce=product,
                    predicted_price=result.get('predicted_price', 0),
                    current_price=product.price if product else result.get('predicted_price', 0),
                    confidence_score=result.get('confidence', 75),
                    demand_level=result.get('demand_level', 'medium'),
                    factors_considered=result.get('analysis', '')[:500],
                    is_active=True
                )
            except Exception as e:
                print(f"Error saving prediction: {e}")
            
            return JsonResponse({
                'success': True,
                'crop': result.get('crop'),
                'location': result.get('location'),
                'analysis': result.get('analysis'),
                'predicted_price': result.get('predicted_price'),
                'confidence': result.get('confidence'),
                'recommendation': result.get('recommendation'),
                'demand_level': result.get('demand_level'),
                'ai_provider': result.get('ai_provider', 'AI Service'),
                'offline_mode': result.get('offline_mode', False),
                'product': product_data
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Prediction failed')
            }, status=500)
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def predict_price_view(request, produce_id):
    """Legacy endpoint for produce ID based prediction"""
    produce = get_object_or_404(Produce, id=produce_id)
    
    if request.method == 'GET':
        result = ai_service.predict_price(produce.name, produce.location)
        
        if result.get('success'):
            return JsonResponse({
                'success': True,
                'crop': produce.name,
                'location': produce.location,
                'current_price': float(produce.price),
                'analysis': result.get('analysis', ''),
                'recommendation': result.get('recommendation', ''),
                'predicted_price': result.get('predicted_price', 0),
                'confidence': result.get('confidence', 75)
            })
        else:
            return JsonResponse({'success': False, 'error': result.get('error', 'Prediction failed')})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def get_crops_list(request):
    """API endpoint to get list of available crops with images"""
    crops = []
    seen_names = set()
    
    for produce in Produce.objects.filter(is_deleted=False).order_by('name'):
        if produce.name not in seen_names:
            seen_names.add(produce.name)
            crops.append({
                'id': produce.id,
                'name': produce.name,
                'price': float(produce.price) if produce.price else 0,
                'image_url': produce.image.url if produce.image else None,
                'unit': produce.unit
            })
            if len(crops) >= 50:
                break
    
    return JsonResponse({
        'success': True,
        'crops': crops
    })

@login_required
def prediction_history(request):
    """API endpoint to get prediction history"""
    days = request.GET.get('days', 30)
    try:
        days = int(days)
    except:
        days = 30
    
    cutoff_date = timezone.now().date() - timedelta(days=days)
    
    predictions = PricePrediction.objects.filter(
        prediction_date__gte=cutoff_date,
        is_active=True
    ).select_related('produce').order_by('-prediction_date')[:50]
    
    history_data = []
    for pred in predictions:
        history_data.append({
            'crop': pred.produce.name if pred.produce else 'General',
            'predicted_price': float(pred.predicted_price),
            'confidence': float(pred.confidence_score),
            'date': pred.prediction_date.strftime('%Y-%m-%d'),
            'demand': pred.demand_level
        })
    
    return JsonResponse({
        'success': True,
        'history': history_data,
        'count': len(history_data)
    })