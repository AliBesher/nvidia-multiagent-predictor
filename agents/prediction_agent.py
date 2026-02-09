"""
Prediction Agent

Manages the ML prediction model for NVIDIA stock price prediction.
Handles training, prediction, and model evaluation.
"""

from typing import Dict, Optional, List
from datetime import datetime

from agents.base_agent import BaseAgent
from models.prediction_model import PredictionModel, MIN_TRAINING_SAMPLES, IDEAL_TRAINING_SAMPLES
from data.database_manager import DatabaseManager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PredictionAgent(BaseAgent):
    """
    Agent responsible for making stock price predictions
    
    Uses Random Forest model with features:
    - Sentiment scores (company, macro, combined)
    - Technical indicators (RSI, MACD)
    - Price momentum
    - Volume patterns
    """
    
    def __init__(self):
        super().__init__(agent_name="PredictionAgent")
        self.model = PredictionModel()
        self.db = DatabaseManager()
        
        logger.info(f"PredictionAgent initialized")
        logger.info(f"  Model trained: {self.model.is_trained}")
        logger.info(f"  Training samples: {self.model.training_samples}")
    
    def train_model(self, force: bool = False) -> Dict:
        """
        Train the prediction model with all available data
        
        Args:
            force: If True, retrain even if model exists
        
        Returns:
            Training result dictionary
        """
        logger.info("="*60)
        logger.info("  Training Prediction Model")
        logger.info("="*60)
        
        # Get all historical data
        all_data = self.db.get_all_daily_data()
        
        if not all_data:
            return {
                'success': False,
                'message': "No data available for training"
            }
        
        # Check if we have enough data
        data_count = len(all_data)
        logger.info(f"Available data: {data_count} days")
        
        if data_count < MIN_TRAINING_SAMPLES:
            logger.warning(f"⚠️  Insufficient data for training")
            logger.warning(f"   Have: {data_count} days")
            logger.warning(f"   Need: {MIN_TRAINING_SAMPLES} days minimum")
            logger.warning(f"   Ideal: {IDEAL_TRAINING_SAMPLES} days")
            return {
                'success': False,
                'message': f"Need {MIN_TRAINING_SAMPLES} days of data (have {data_count})",
                'data_count': data_count,
                'required': MIN_TRAINING_SAMPLES
            }
        
        # Check if model already trained and force not set
        if self.model.is_trained and not force:
            logger.info(f"Model already trained ({self.model.training_samples} samples)")
            logger.info(f"Use force=True to retrain")
            return {
                'success': True,
                'message': "Model already trained",
                'samples': self.model.training_samples,
                'accuracy': self.model.accuracy
            }
        
        # Train model
        result = self.model.train(all_data)
        
        if result['success']:
            logger.info(f"✓ Model trained successfully")
            logger.info(f"  Samples: {result['samples']}")
            logger.info(f"  Accuracy: {result['accuracy']:.1%}")
            
            if data_count < IDEAL_TRAINING_SAMPLES:
                logger.info(f"  Note: Accuracy will improve with more data")
                logger.info(f"  ({data_count}/{IDEAL_TRAINING_SAMPLES} ideal samples)")
        else:
            logger.error(f"✗ Training failed: {result['message']}")
        
        return result
    
    def predict_next_day(self, date: Optional[str] = None) -> Dict:
        """
        Predict next day's price movement using Tail and Head Theory with Technical Inertia
        
        Args:
            date: Date to predict for (default: latest in database)
        
        Returns:
            Prediction result dictionary with physics-based reasoning
        """
        logger.info("-"*60)
        logger.info("🔮 GENERATING PHYSICS-BASED PREDICTION")
        logger.info("-"*60)
        
        # Check if model is trained
        if not self.model.is_trained:
            logger.warning("Model not trained - attempting to train first")
            train_result = self.train_model()
            if not train_result['success']:
                return {
                    'success': False,
                    'prediction': None,
                    'message': f"Cannot predict - {train_result['message']}"
                }
        
        # Get the latest data for prediction
        if date:
            current_data = self.db.get_daily_data(date)
        else:
            current_data = self.db.get_latest_daily_data()
        
        if not current_data:
            return {
                'success': False,
                'prediction': None,
                'message': "No gravitational data available for prediction"
            }
        
        logger.info(f"📊 Analyzing gravitational field for: {current_data.get('date', 'latest')}")
        logger.info(f"  Price: ${float(current_data.get('close_price', 0)):.2f}")
        logger.info(f"  Sentiment Field: {float(current_data.get('sentiment_score', 0)):.2f}")
        logger.info(f"  Probability Range: {current_data.get('sentiment_range', 'N/A')}")
        logger.info(f"  Entropy Level: {current_data.get('entropy', 'N/A')}")
        logger.info(f"  Technical Momentum (RSI): {float(current_data.get('rsi', 0)):.2f}")
        
        # Get average volume for gravitational context
        avg_volume = self.db.get_average_volume(days=20)
        current_data['avg_volume'] = avg_volume
        
        # Generate physics-based prediction with Technical Inertia
        prediction = self.generate_prediction(current_data)
        
        if prediction['can_predict']:
            logger.info(f"\n🎯 GRAVITATIONAL PREDICTION: {prediction['prediction']}")
            logger.info(f"   Final Confidence: {prediction['confidence']:.1%}")
            logger.info(f"   Range Confidence: {prediction.get('range_confidence', 0):.1%} (field focus)")
            logger.info(f"   Technical Inertia: {prediction.get('technical_inertia', 0):.2f} (momentum resistance)")
            logger.info(f"   Physics Analysis: {prediction.get('physics_reasoning', 'N/A')}")
            logger.info(f"   Up probability: {prediction['probability_up']:.1%}")
            logger.info(f"   Down probability: {prediction['probability_down']:.1%}")
            logger.info(f"   Probability Field Width: {prediction.get('range_width', 0):.1f}")
            
            # Enhanced physics-based warnings
            entropy = prediction.get('entropy_level', 'Medium')
            if entropy == 'High':
                logger.warning("⚠️  HIGH ENTROPY FIELD DETECTED:")
                logger.warning("   Gravitational forces are chaotic and dispersed")
                logger.warning("   Probability field lacks coherent structure")
                logger.warning("   Consider waiting for entropy reduction")
            
            inertia_override = prediction.get('inertia_override', False)
            if inertia_override:
                logger.info("✨ INERTIA OVERRIDE: Sentiment mass sufficient to change trajectory")
            elif prediction.get('technical_inertia', 0) > 0.7:
                logger.warning("🛡️  HIGH TECHNICAL INERTIA: Strong momentum resistance detected")
            
            # Save prediction to database
            self.db.save_prediction(
                date=str(current_data.get('date', datetime.now().strftime('%Y-%m-%d'))),
                prediction=prediction['prediction'],
                confidence=prediction['confidence']
            )
        else:
            logger.warning(f"Cannot generate prediction: {prediction['message']}")
        
        return {
            'success': prediction['can_predict'],
            'date': str(current_data.get('date', '')),
            'prediction': prediction['prediction'],
            'confidence': prediction['confidence'],
            'probability_up': prediction['probability_up'],
            'probability_down': prediction['probability_down'],
            'entropy': current_data.get('entropy', 'Medium'),
            'entropy_level': prediction.get('entropy_level', 'Medium'),
            'sentiment_range': current_data.get('sentiment_range', '0 to 0'),
            'range_width': prediction.get('range_width', 0.0),
            'range_confidence': prediction.get('range_confidence', 0.5),
            'technical_inertia': prediction.get('technical_inertia', 0.0),
            'inertia_override': prediction.get('inertia_override', False),
            'physics_reasoning': prediction.get('physics_reasoning', ''),
            'message': prediction['message']
        }
    
    def _calculate_range_width(self, sentiment_range: str) -> float:
        """
        Calculate the width of a sentiment probability range
        
        Args:
            sentiment_range: Range string like "-10 to +20" or "65 to 75"
            
        Returns:
            Width of the range as a float
        """
        try:
            # Parse range string
            if ' to ' in sentiment_range:
                parts = sentiment_range.split(' to ')
                if len(parts) == 2:
                    # Remove any + signs and convert to float
                    low = float(parts[0].replace('+', ''))
                    high = float(parts[1].replace('+', ''))
                    return abs(high - low)
            return 0.0
        except (ValueError, AttributeError):
            return 0.0
    
    def generate_prediction(self, current_data: Dict) -> Dict:
        """
        Generate physics-based prediction with Technical Inertia integration.
        Implements Tail and Head Theory with gravitational field analysis.
        
        Args:
            current_data: Current market and sentiment data
        
        Returns:
            Enhanced prediction with physics reasoning
        """
        # Get base prediction from model
        base_prediction = self.model.predict(current_data)
        
        if not base_prediction['can_predict']:
            return base_prediction
        
        # Extract technical indicators for inertia calculation
        rsi = float(current_data.get('rsi', 50))
        moving_avg_50 = float(current_data.get('moving_avg_50', 0))
        current_price = float(current_data.get('close_price', 0))
        sentiment_score = float(current_data.get('sentiment_score', 0))
        
        # Get sentiment physics data
        entropy = current_data.get('entropy', 'Medium')
        sentiment_range = current_data.get('sentiment_range', '0 to 0')
        
        # Calculate Technical Inertia
        technical_inertia = self._calculate_technical_inertia(rsi, current_price, moving_avg_50)
        
        # Calculate Range-based Confidence
        range_width = self._calculate_range_width(sentiment_range)
        range_confidence = self._calculate_range_confidence(range_width)
        
        # Apply Technical Inertia to prediction logic
        prediction_result = self._apply_technical_inertia(
            base_prediction, technical_inertia, sentiment_score, entropy
        )
        
        # Generate physics-based reasoning
        physics_reasoning = self._generate_physics_reasoning(
            technical_inertia, range_width, entropy, sentiment_score, rsi
        )
        
        # Combine all confidence factors
        final_confidence = self._calculate_final_confidence(
            base_prediction['confidence'], range_confidence, entropy, technical_inertia
        )
        
        # Update prediction with physics enhancements
        prediction_result.update({
            'confidence': final_confidence,
            'range_width': range_width,
            'range_confidence': range_confidence,
            'technical_inertia': technical_inertia,
            'physics_reasoning': physics_reasoning,
            'entropy_level': entropy
        })
        
        logger.info(f"🧲 Technical Inertia: {technical_inertia:.2f} (momentum resistance)")
        logger.info(f"📏 Range Width: {range_width:.1f} (probability field dispersion)")
        logger.info(f"🎯 Range Confidence: {range_confidence:.1%} (field focus factor)")
        logger.info(f"⚡ Physics Reasoning: {physics_reasoning}")
        
        return prediction_result
    
    def _calculate_technical_inertia(self, rsi: float, price: float, moving_avg: float) -> float:
        """
        Calculate Technical Inertia - resistance to trend changes based on momentum.
        Higher inertia requires stronger news 'Mass' to overcome.
        
        Args:
            rsi: Relative Strength Index (0-100)
            price: Current price
            moving_avg: 50-day moving average
        
        Returns:
            Technical inertia score (0-1, higher = more resistance to change)
        """
        # RSI momentum component (0-1)
        if rsi > 70:  # Overbought - high upward inertia
            rsi_inertia = (rsi - 70) / 30  # 0 to 1 as RSI goes 70-100
        elif rsi < 30:  # Oversold - high downward inertia  
            rsi_inertia = (30 - rsi) / 30  # 0 to 1 as RSI goes 30-0
        else:
            rsi_inertia = 0  # Neutral zone - low inertia
        
        # Price vs moving average momentum (0-1)
        if moving_avg > 0:
            price_deviation = abs(price - moving_avg) / moving_avg
            trend_inertia = min(price_deviation * 2, 1.0)  # Cap at 1.0
        else:
            trend_inertia = 0
        
        # Combine factors (weight RSI more heavily)
        technical_inertia = (rsi_inertia * 0.7) + (trend_inertia * 0.3)
        
        return min(technical_inertia, 1.0)
    
    def _calculate_range_confidence(self, range_width: float) -> float:
        """
        Calculate confidence based on sentiment range width.
        Narrower range = higher confidence (focused gravitational field).
        
        Args:
            range_width: Width of sentiment probability range
        
        Returns:
            Confidence factor (0-1)
        """
        if range_width <= 0:
            return 0.5  # Default for missing data
        
        # Narrow ranges give high confidence, wide ranges give low confidence
        # Use exponential decay for smoother scaling
        import math
        confidence = math.exp(-range_width / 20)  # Decay factor of 20
        
        return max(min(confidence, 0.95), 0.2)  # Clamp between 20% and 95%
    
    def _apply_technical_inertia(self, base_prediction: Dict, technical_inertia: float, 
                                sentiment_score: float, entropy: str) -> Dict:
        """
        Apply Technical Inertia to modify prediction based on momentum resistance.
        High inertia requires strong sentiment mass to predict reversals.
        """
        prediction = base_prediction.copy()
        
        # Calculate required sentiment strength to overcome inertia
        inertia_threshold = technical_inertia * 60  # Scale to sentiment range
        sentiment_strength = abs(sentiment_score)
        
        # If sentiment is not strong enough to overcome inertia, bias toward continuation
        if sentiment_strength < inertia_threshold:
            # High inertia + weak sentiment = trend continuation bias
            inertia_factor = 1 - (sentiment_strength / inertia_threshold)
            
            # Reduce confidence in reversal predictions
            if ((sentiment_score > 0 and prediction['prediction'] == 'DOWN') or 
                (sentiment_score < 0 and prediction['prediction'] == 'UP')):
                # Trying to predict reversal against inertia
                prediction['confidence'] *= (1 - inertia_factor * 0.4)  # Reduce confidence
                prediction['inertia_override'] = False
            else:
                # Predicting continuation with inertia
                prediction['confidence'] *= (1 + inertia_factor * 0.2)  # Boost confidence
                prediction['inertia_override'] = False
        else:
            # Strong sentiment can overcome inertia
            prediction['inertia_override'] = True
        
        return prediction
    
    def _generate_physics_reasoning(self, technical_inertia: float, range_width: float, 
                                   entropy: str, sentiment_score: float, rsi: float) -> str:
        """
        Generate physics-based reasoning using gravitational field terminology.
        """
        reasoning_parts = []
        
        # Range width analysis (probability field)
        if range_width > 30:
            reasoning_parts.append("The probability field is too wide due to high entropy")
        elif range_width < 10:
            reasoning_parts.append("The gravitational pull is concentrated at the head")
        else:
            reasoning_parts.append("The probability field shows moderate dispersion")
        
        # Technical inertia analysis
        if technical_inertia > 0.7:
            if rsi > 70:
                reasoning_parts.append("Strong upward momentum creates resistance to downward forces")
            elif rsi < 30:
                reasoning_parts.append("Strong downward momentum creates resistance to upward forces")
            else:
                reasoning_parts.append("High technical inertia requires exceptional news mass to alter trajectory")
        elif technical_inertia < 0.3:
            reasoning_parts.append("Low technical inertia allows sentiment forces to dominate price movement")
        
        # Sentiment field strength
        if abs(sentiment_score) > 40:
            reasoning_parts.append(f"Powerful {'positive' if sentiment_score > 0 else 'negative'} gravitational field detected")
        elif abs(sentiment_score) < 10:
            reasoning_parts.append("Weak gravitational field suggests minimal directional force")
        
        # Entropy contribution
        if entropy == 'High':
            reasoning_parts.append("High entropy indicates chaotic information dispersion")
        elif entropy == 'Low':
            reasoning_parts.append("Low entropy suggests coherent information alignment")
        
        return ". ".join(reasoning_parts) + "."
    
    def _calculate_final_confidence(self, base_confidence: float, range_confidence: float, 
                                   entropy: str, technical_inertia: float) -> float:
        """
        Calculate final confidence by combining all physics factors.
        """
        # Start with range-based confidence (most important)
        final_confidence = range_confidence
        
        # Apply entropy adjustment
        if entropy == 'Low':
            final_confidence *= 1.15  # Boost for low entropy
        elif entropy == 'High':
            final_confidence *= 0.85  # Reduce for high entropy
        
        # Apply inertia adjustment (higher inertia = more confident in continuation)
        inertia_adjustment = 1 + (technical_inertia * 0.1)  # Small boost for high inertia
        final_confidence *= inertia_adjustment
        
        # Combine with base model confidence (weighted average)
        final_confidence = (final_confidence * 0.7) + (base_confidence * 0.3)
        
        return max(min(final_confidence, 0.95), 0.15)  # Clamp between 15% and 95%
    
    def get_model_status(self) -> Dict:
        """Get current model status"""
        status = self.model.get_status()
        
        # Add database info
        data_count = self.db.get_data_count()
        status['database_records'] = data_count
        status['can_train'] = data_count >= MIN_TRAINING_SAMPLES
        
        # Progress to ideal
        if data_count < IDEAL_TRAINING_SAMPLES:
            status['progress'] = f"{data_count}/{IDEAL_TRAINING_SAMPLES} days ({data_count/IDEAL_TRAINING_SAMPLES*100:.0f}%)"
        else:
            status['progress'] = f"{data_count} days (ready for production)"
        
        return status
    
    def evaluate_predictions(self, days: int = 30) -> Dict:
        """
        Evaluate prediction accuracy over recent days
        
        Args:
            days: Number of days to evaluate
        
        Returns:
            Evaluation results
        """
        logger.info(f"Evaluating predictions for last {days} days")
        
        # Get predictions with actual results
        predictions = self.db.get_predictions_with_results(days)
        
        if not predictions:
            return {
                'success': False,
                'message': "No predictions with results available",
                'accuracy': 0.0
            }
        
        correct = 0
        total = 0
        
        for p in predictions:
            if p.get('prediction') and p.get('actual_direction'):
                total += 1
                if p['prediction'] == p['actual_direction']:
                    correct += 1
        
        if total == 0:
            return {
                'success': False,
                'message': "No completed predictions to evaluate",
                'accuracy': 0.0
            }
        
        accuracy = correct / total
        
        logger.info(f"Evaluation results:")
        logger.info(f"  Correct: {correct}/{total}")
        logger.info(f"  Accuracy: {accuracy:.1%}")
        
        return {
            'success': True,
            'correct': correct,
            'total': total,
            'accuracy': accuracy,
            'message': f"Accuracy: {accuracy:.1%} ({correct}/{total})"
        }


# Test function
if __name__ == "__main__":
    print("Testing PredictionAgent...")
    
    agent = PredictionAgent()
    
    # Get status
    status = agent.get_model_status()
    print(f"\nModel Status:")
    print(f"  Trained: {status['is_trained']}")
    print(f"  Database records: {status['database_records']}")
    print(f"  Progress: {status['progress']}")
    
    # Try to train
    if status['can_train']:
        print("\nTraining model...")
        result = agent.train_model(force=True)
        print(f"  Result: {result['message']}")
        
        # Try prediction
        if result['success']:
            print("\nMaking prediction...")
            pred = agent.predict_next_day()
            print(f"  Prediction: {pred['prediction']}")
            print(f"  Confidence: {pred['confidence']:.1%}")
    else:
        print(f"\nNot enough data to train (need {MIN_TRAINING_SAMPLES})")
