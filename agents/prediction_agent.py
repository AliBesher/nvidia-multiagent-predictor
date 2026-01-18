"""
Prediction Agent

Manages the ML prediction model for NVIDIA stock price prediction.
Handles training, prediction, and model evaluation.
"""

from typing import Dict, Optional, List
from datetime import datetime

from agents.base_agent import BaseAgent
from models.prediction_model import PredictionModel, MIN_TRAINING_SAMPLES, IDEAL_TRAINING_SAMPLES
from utils.database_manager import DatabaseManager
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
        Predict next day's price movement
        
        Args:
            date: Date to predict for (default: latest in database)
        
        Returns:
            Prediction result dictionary
        """
        logger.info("-"*60)
        logger.info("Making prediction for next trading day")
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
                'message': "No data available for prediction"
            }
        
        logger.info(f"Predicting based on: {current_data.get('date', 'latest')}")
        logger.info(f"  Close: ${float(current_data.get('close_price', 0)):.2f}")
        logger.info(f"  Sentiment: {float(current_data.get('sentiment_score', 0)):.2f}")
        logger.info(f"  RSI: {float(current_data.get('rsi', 0)):.2f}")
        
        # Get average volume for context
        avg_volume = self.db.get_average_volume(days=20)
        current_data['avg_volume'] = avg_volume
        
        # Make prediction
        prediction = self.model.predict(current_data)
        
        if prediction['can_predict']:
            logger.info(f"\n🎯 PREDICTION: {prediction['prediction']}")
            logger.info(f"   Confidence: {prediction['confidence']:.1%}")
            logger.info(f"   Up probability: {prediction['probability_up']:.1%}")
            logger.info(f"   Down probability: {prediction['probability_down']:.1%}")
            
            # Save prediction to database
            self.db.save_prediction(
                date=str(current_data.get('date', datetime.now().strftime('%Y-%m-%d'))),
                prediction=prediction['prediction'],
                confidence=prediction['confidence']
            )
        else:
            logger.warning(f"Cannot make prediction: {prediction['message']}")
        
        return {
            'success': prediction['can_predict'],
            'date': str(current_data.get('date', '')),
            'prediction': prediction['prediction'],
            'confidence': prediction['confidence'],
            'probability_up': prediction['probability_up'],
            'probability_down': prediction['probability_down'],
            'message': prediction['message']
        }
    
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
