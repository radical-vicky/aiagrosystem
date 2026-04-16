import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
from datetime import datetime
import os

class PricePredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
    
    def prepare_features(self, historical_orders):
        """Prepare features for price prediction"""
        if len(historical_orders) < 10:
            return None, None
        
        features = []
        prices = []
        
        for order in historical_orders:
            day_of_week = order.order_date.weekday()
            month = order.order_date.month
            quantity = float(order.quantity)
            price = float(order.total_price / quantity)
            
            features.append([day_of_week, month, quantity])
            prices.append(price)
        
        return np.array(features), np.array(prices)
    
    def train_model(self, produce_id, historical_orders):
        """Train Random Forest model for price prediction"""
        features, prices = self.prepare_features(historical_orders)
        
        if features is None:
            return None
        
        features_scaled = self.scaler.fit_transform(features)
        
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model.fit(features_scaled, prices)
        
        # Create models directory if it doesn't exist
        os.makedirs('models', exist_ok=True)
        
        joblib.dump(self.model, f'models/price_predictor_{produce_id}.pkl')
        joblib.dump(self.scaler, f'models/scaler_{produce_id}.pkl')
        
        return self.model
    
    def predict_price(self, produce_id, historical_orders):
        """Predict future price for produce"""
        try:
            self.model = joblib.load(f'models/price_predictor_{produce_id}.pkl')
            self.scaler = joblib.load(f'models/scaler_{produce_id}.pkl')
        except:
            self.train_model(produce_id, historical_orders)
            if self.model is None:
                return None
        
        current_date = datetime.now()
        features = np.array([[
            current_date.weekday(),
            current_date.month,
            100
        ]])
        
        features_scaled = self.scaler.transform(features)
        predicted_price = self.model.predict(features_scaled)[0]
        
        confidence = min(95, len(self.model.feature_importances_) * 20)
        
        return {
            'predicted_price': round(predicted_price, 2),
            'confidence_score': round(confidence, 2)
        }

predictor = PricePredictor()