import os
import re
from django.conf import settings
from datetime import datetime

class RealAIService:
    """Groq-powered market intelligence service (Free)"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'GROQ_API_KEY', None) or os.environ.get('GROQ_API_KEY')
        self.client = None
        
        if self.api_key and self.api_key.startswith('gsk_'):
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
                print(f"✅ Groq client initialized successfully (Free Tier)")
            except Exception as e:
                print(f"❌ Failed to initialize Groq client: {e}")
                self.client = None
        else:
            print(f"❌ Invalid or missing Groq API key")
    
    def predict_price(self, crop_type, location):
        """Get AI prediction from Groq"""
        
        # Try API if client is available
        if self.client:
            try:
                result = self._call_groq(crop_type, location)
                if result and result.get('success'):
                    return result
            except Exception as e:
                print(f"Groq API error: {e}")
                # Fall through to local prediction
        
        # Use local prediction
        return self._local_prediction(crop_type, location, api_available=bool(self.client))
    
    def _call_groq(self, crop_type, location):
        """Call Groq API (Free) - Using current supported models"""
        try:
            current_date = datetime.now().strftime('%B %d, %Y')
            current_month = datetime.now().strftime('%B')
            
            prompt = f"""You are an agricultural market analyst AI specializing in Kenya's agricultural markets, particularly in {location}.

Provide a detailed price prediction and market analysis for {crop_type} in {location}, Kenya.

Current date: {current_date}

Please provide your response in the following format:

**Current Market Price:** KES [amount] per kg
**Predicted Price (Next Month):** KES [amount] per kg
**Best Time to Sell:** [specific time frame]
**Confidence Level:** [percentage]%

**Market Analysis:**
[2-3 paragraph detailed analysis including supply/demand dynamics, seasonal patterns, and local market conditions]

**Key Factors Affecting Prices:**
• Factor 1 with specific details
• Factor 2 with specific details
• Factor 3 with specific details

**Recommendation for Farmers:**
[Actionable advice for farmers in {location}]

Keep your response practical for small-scale farmers in Kenya. Be specific with prices and timing. Base your analysis on {current_month} market conditions."""

            # Updated to use current supported models
            # Options: "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Current supported model
                messages=[
                    {"role": "system", "content": "You are an expert agricultural market analyst for Kenyan farmers. Provide practical, data-driven insights based on real market conditions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            analysis = response.choices[0].message.content
            
            # Parse the response to extract structured data
            parsed = self._parse_ai_response(analysis, crop_type)
            
            return {
                'success': True,
                'crop': crop_type,
                'location': location,
                'analysis': analysis,
                'predicted_price': parsed['predicted_price'],
                'confidence': parsed['confidence'],
                'recommendation': parsed['recommendation'],
                'demand_level': parsed['demand_level'],
                'ai_provider': 'Groq Llama 3.3 (Free)',
                'offline_mode': False
            }
            
        except Exception as e:
            print(f"Groq call failed: {e}")
            return None
    
    def _parse_ai_response(self, analysis, crop_type):
        """Parse AI response to extract structured data"""
        
        # Extract price
        price_match = re.search(r'Predicted Price.*?KES\s*(\d+(?:\.\d+)?)', analysis, re.IGNORECASE)
        if not price_match:
            price_match = re.search(r'KES\s*(\d+(?:\.\d+)?)', analysis)
        predicted_price = float(price_match.group(1)) if price_match else self._get_base_price(crop_type)
        
        # Extract confidence
        confidence_match = re.search(r'Confidence Level:\s*(\d+)%', analysis, re.IGNORECASE)
        confidence = int(confidence_match.group(1)) if confidence_match else 75
        
        # Extract recommendation
        rec_match = re.search(r'Recommendation for Farmers:?\s*(.*?)(?:\n\n|\n\*\*|$)', analysis, re.DOTALL | re.IGNORECASE)
        if not rec_match:
            rec_match = re.search(r'\*\*Recommendation[^*]*\*\*\s*(.*?)(?:\n\n|\n\*\*|$)', analysis, re.DOTALL)
        recommendation = rec_match.group(1).strip()[:500] if rec_match else self._get_default_recommendation(crop_type)
        
        # Determine demand level
        analysis_lower = analysis.lower()
        if 'high demand' in analysis_lower or 'prices expected to rise' in analysis_lower:
            demand_level = 'high'
        elif 'low demand' in analysis_lower or 'prices expected to drop' in analysis_lower:
            demand_level = 'low'
        else:
            demand_level = 'medium'
        
        return {
            'predicted_price': predicted_price,
            'confidence': confidence,
            'recommendation': recommendation,
            'demand_level': demand_level
        }
    
    def _get_base_price(self, crop_type):
        """Get base price for crop type"""
        prices = {
            'maize': 45, 'tomatoes': 80, 'potatoes': 65, 'onions': 70,
            'cabbage': 45, 'kale': 25, 'sukuma wiki': 25, 'carrots': 90,
            'avocado': 60, 'mangoes': 100, 'beans': 130, 'rice': 120,
            'wheat': 55, 'spinach': 30, 'capsicum': 150
        }
        crop_lower = crop_type.lower()
        for key in prices:
            if key in crop_lower:
                return prices[key]
        return 50
    
    def _get_default_recommendation(self, crop_type):
        """Get default recommendation based on crop"""
        crop_lower = crop_type.lower()
        recommendations = {
            'maize': "Store your maize in a dry, ventilated area. Prices typically rise 2-3 weeks after harvest.",
            'tomato': "Sell tomatoes within 3-5 days of harvest. Consistent supply secures better prices.",
            'potato': "Store potatoes in a cool, dark place. Prices improve 3-4 weeks after harvest.",
            'onion': "Cure onions properly before storage. Well-cured onions store for 3-4 months.",
            'cabbage': "Harvest and sell quickly as cabbages don't store well.",
            'kale': "Harvest regularly to maintain production. Daily delivery ensures stable income.",
            'carrot': "Wash and grade carrots before selling. Sorted carrots achieve higher prices.",
            'avocado': "Harvest at correct maturity. Size grading significantly impacts pricing.",
        }
        for key in recommendations:
            if key in crop_lower:
                return recommendations[key]
        return "Monitor local market prices daily. Build relationships with multiple buyers."
    
    def _local_prediction(self, crop_type, location, api_available=True):
        """Fallback local prediction when API is unavailable"""
        current_month = datetime.now().month
        current_year = datetime.now().year
        month_name = datetime.now().strftime('%B')
        
        base_price = self._get_base_price(crop_type)
        
        # Seasonal adjustments
        if current_month in [1, 2, 12]:
            seasonal_factor = 1.15
            trend = "rising"
            advice = "Hold your produce for 2-3 weeks. Prices typically increase."
            demand = "high"
        elif current_month in [6, 7, 8]:
            seasonal_factor = 0.85
            trend = "stable to slightly lower"
            advice = "Consider selling now. Prices are at seasonal lows."
            demand = "low"
        else:
            seasonal_factor = 1.0
            trend = "stable"
            advice = "Monitor market prices and sell when you get a good offer."
            demand = "medium"
        
        predicted_price = round(base_price * seasonal_factor, 2)
        
        api_note = ""
        if not api_available:
            api_note = "\n\n---\n⚠️ **Note:** Groq API not configured. Get free API key at console.groq.com"
        
        analysis = f"""📊 **MARKET ANALYSIS FOR {crop_type.upper()} IN {location.upper()}**

As of {month_name} {current_year}, the {crop_type} market is showing {trend} prices.

💰 **Current Market Price:** KES {base_price} per kg
📈 **Predicted Price (Next Month):** KES {predicted_price} per kg
⏰ **Best Time to Sell:** {advice}
🎯 **Confidence Level:** {75 if seasonal_factor == 1 else 85}%

**Market Analysis:**
The {crop_type} market is in {'peak demand' if seasonal_factor > 1 else 'off-peak' if seasonal_factor < 1 else 'normal'} season.

**Key Factors Affecting Prices:**
• Seasonal patterns: {seasonal_factor * 100:.0f}% of normal prices
• Local supply and demand in {location}
• Transportation costs to major markets

**Recommendation for Farmers:**
{advice} Quality produce achieves better prices.{api_note}"""
        
        return {
            'success': True,
            'crop': crop_type,
            'location': location,
            'analysis': analysis,
            'predicted_price': predicted_price,
            'confidence': 75 if seasonal_factor == 1 else 85,
            'recommendation': advice,
            'demand_level': demand,
            'ai_provider': 'Local AI (Offline Mode)',
            'offline_mode': not api_available
        }

# Create singleton instance
ai_service = RealAIService()