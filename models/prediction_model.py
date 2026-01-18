"""
NVIDIA Stock Prediction Model

Simple Random Forest model for predicting next-day price movement.
Designed to work with limited data and improve as more data accumulates.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple, List
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import joblib
import os
from datetime import datetime

from utils.logger import setup_logger

logger = setup_logger(__name__)

# Minimum data required for training
MIN_TRAINING_SAMPLES = 10  # Minimum to start (for testing)
IDEAL_TRAINING_SAMPLES = 100  # Ideal for good predictions


class PredictionModel:
    """
    Random Forest model for predicting stock price movement
    
    Predicts: UP (1) or DOWN (0) for next trading day
    
    Features used:
    - sentiment_score (combined sentiment)
    - company_sentiment
    - macro_sentiment  
    - rsi (Relative Strength Index)
    - macd (MACD value)
    - price_change_percent (today's change)
    - volume_change (volume vs average)
    """
    
    def __init__(self, model_path: str = "models/trained_model.pkl"):
        self.model_path = model_path
        self.model: Optional[RandomForestClassifier] = None
        self.scaler = StandardScaler()
        self.feature_names = [
            'sentiment_score',
            'company_sentiment', 
            'macro_sentiment',
            'rsi',
            'macd',
            'price_change_percent',
            'volume_ratio'
        ]
        self.is_trained = False
        self.training_samples = 0
        self.accuracy = 0.0
        
        # Try to load existing model
        self._load_model()
        
        logger.info(f"PredictionModel initialized (trained: {self.is_trained})")
    
    def _load_model(self) -> bool:
        """Load trained model from disk if exists"""
        try:
            if os.path.exists(self.model_path):
                data = joblib.load(self.model_path)
                self.model = data['model']
                self.scaler = data['scaler']
                self.is_trained = True
                self.training_samples = data.get('training_samples', 0)
                self.accuracy = data.get('accuracy', 0.0)
                logger.info(f"Loaded trained model ({self.training_samples} samples, {self.accuracy:.1%} accuracy)")
                return True
        except Exception as e:
            logger.warning(f"Could not load model: {e}")
        return False
    
    def _save_model(self) -> bool:
        """Save trained model to disk"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            data = {
                'model': self.model,
                'scaler': self.scaler,
                'training_samples': self.training_samples,
                'accuracy': self.accuracy,
                'trained_at': datetime.now().isoformat()
            }
            joblib.dump(data, self.model_path)
            logger.info(f"Model saved to {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False
    
    def prepare_features(self, data: List[Dict]) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Prepare features and labels from database records
        
        Args:
            data: List of daily_data records from database
        
        Returns:
            Tuple of (features array, labels array) or (None, None) if insufficient data
        """
        if len(data) < MIN_TRAINING_SAMPLES:
            logger.warning(f"Insufficient data: {len(data)} records (need {MIN_TRAINING_SAMPLES})")
            return None, None
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(data)
        
        # Calculate derived features
        features_list = []
        labels_list = []
        
        # Calculate average volume for volume ratio
        avg_volume = df['volume'].mean() if 'volume' in df.columns else 1
        
        for i, row in df.iterrows():
            # Skip rows without next_day_close (can't calculate label)
            if row.get('next_day_close') is None or row.get('close_price') is None:
                continue
            
            # Calculate label: 1 if price went up, 0 if down
            next_close = float(row['next_day_close'])
            current_close = float(row['close_price'])
            label = 1 if next_close > current_close else 0
            
            # Calculate price change percent for today
            open_price = float(row.get('open_price', current_close))
            price_change = ((current_close - open_price) / open_price * 100) if open_price > 0 else 0
            
            # Volume ratio
            volume = float(row.get('volume', avg_volume))
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1
            
            # Build feature vector
            features = [
                float(row.get('sentiment_score', 0) or 0),
                float(row.get('company_sentiment', 0) or 0),
                float(row.get('macro_sentiment', 0) or 0),
                float(row.get('rsi', 50) or 50),  # Default RSI to neutral
                float(row.get('macd', 0) or 0),
                price_change,
                volume_ratio
            ]
            
            features_list.append(features)
            labels_list.append(label)
        
        if len(features_list) < MIN_TRAINING_SAMPLES:
            logger.warning(f"Not enough valid samples: {len(features_list)}")
            return None, None
        
        return np.array(features_list), np.array(labels_list)
    
    def train(self, data: List[Dict]) -> Dict:
        """
        Train the prediction model
        
        Args:
            data: List of daily_data records from database
        
        Returns:
            Training results dictionary
        """
        result = {
            'success': False,
            'samples': 0,
            'accuracy': 0.0,
            'message': ''
        }
        
        # Prepare features
        X, y = self.prepare_features(data)
        
        if X is None or y is None:
            result['message'] = f"Insufficient data for training (have {len(data)}, need {MIN_TRAINING_SAMPLES})"
            logger.warning(result['message'])
            return result
        
        try:
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Create and train model
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=5,  # Limit depth to prevent overfitting with small data
                min_samples_split=3,
                min_samples_leaf=2,
                random_state=42,
                class_weight='balanced'  # Handle imbalanced classes
            )
            
            # Cross-validation for accuracy estimate
            if len(X) >= 10:
                cv_folds = min(5, len(X) // 2)
                scores = cross_val_score(self.model, X_scaled, y, cv=cv_folds)
                self.accuracy = scores.mean()
            else:
                self.accuracy = 0.5  # Can't reliably estimate with very small data
            
            # Train on full data
            self.model.fit(X_scaled, y)
            
            self.is_trained = True
            self.training_samples = len(X)
            
            # Save model
            self._save_model()
            
            result['success'] = True
            result['samples'] = self.training_samples
            result['accuracy'] = self.accuracy
            result['message'] = f"Model trained on {self.training_samples} samples"
            
            # Log feature importance
            importance = dict(zip(self.feature_names, self.model.feature_importances_))
            sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
            logger.info("Feature importance:")
            for name, imp in sorted_importance:
                logger.info(f"  {name}: {imp:.3f}")
            
            return result
            
        except Exception as e:
            result['message'] = f"Training failed: {str(e)}"
            logger.error(result['message'])
            return result
    
    def predict(self, current_data: Dict) -> Dict:
        """
        Predict next day's price movement
        
        Args:
            current_data: Today's data (from database or real-time)
        
        Returns:
            Prediction result dictionary
        """
        result = {
            'prediction': None,  # 'UP' or 'DOWN'
            'confidence': 0.0,
            'probability_up': 0.0,
            'probability_down': 0.0,
            'can_predict': False,
            'message': ''
        }
        
        if not self.is_trained or self.model is None:
            result['message'] = "Model not trained yet"
            return result
        
        try:
            # Prepare single sample features
            avg_volume = current_data.get('avg_volume', current_data.get('volume', 1))
            open_price = float(current_data.get('open_price', current_data.get('close_price', 1)))
            close_price = float(current_data.get('close_price', 1))
            
            price_change = ((close_price - open_price) / open_price * 100) if open_price > 0 else 0
            volume_ratio = float(current_data.get('volume', avg_volume)) / avg_volume if avg_volume > 0 else 1
            
            features = np.array([[
                float(current_data.get('sentiment_score', 0) or 0),
                float(current_data.get('company_sentiment', 0) or 0),
                float(current_data.get('macro_sentiment', 0) or 0),
                float(current_data.get('rsi', 50) or 50),
                float(current_data.get('macd', 0) or 0),
                price_change,
                volume_ratio
            ]])
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Get prediction and probabilities
            prediction = self.model.predict(features_scaled)[0]
            probabilities = self.model.predict_proba(features_scaled)[0]
            
            result['prediction'] = 'UP' if prediction == 1 else 'DOWN'
            result['probability_up'] = probabilities[1] if len(probabilities) > 1 else probabilities[0]
            result['probability_down'] = probabilities[0] if len(probabilities) > 1 else 1 - probabilities[0]
            result['confidence'] = max(result['probability_up'], result['probability_down'])
            result['can_predict'] = True
            result['message'] = f"Prediction: {result['prediction']} ({result['confidence']:.1%} confidence)"
            
            return result
            
        except Exception as e:
            result['message'] = f"Prediction failed: {str(e)}"
            logger.error(result['message'])
            return result
    
    def get_status(self) -> Dict:
        """Get model status summary"""
        return {
            'is_trained': self.is_trained,
            'training_samples': self.training_samples,
            'accuracy': self.accuracy,
            'min_required': MIN_TRAINING_SAMPLES,
            'ideal_samples': IDEAL_TRAINING_SAMPLES,
            'features': self.feature_names,
            'ready_for_prediction': self.is_trained and self.training_samples >= MIN_TRAINING_SAMPLES
        }
