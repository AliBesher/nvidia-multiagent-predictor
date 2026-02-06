"""
Analysis Utilities for NVIDIA Stock Prediction System
Contains utility functions for measuring model performance and calibration
"""

from typing import Optional, Dict, List
from utils.logger import setup_logger

logger = setup_logger(__name__)


def calculate_gravity_accuracy(predicted_score: float, price_change_percent: float) -> float:
    """
    Calculate accuracy of the Informational Gravity model prediction
    
    Measures how well the gravity-based sentiment score predicts actual market movement.
    The predicted_score represents the 'Head' (point score) from the gravity analysis,
    normalized to match the price movement scale.
    
    Args:
        predicted_score: Gravity-based sentiment score (-100 to +100)
        price_change_percent: Actual stock price change percentage
        
    Returns:
        Accuracy percentage (0-100) representing 'Physical Match' between theory and reality
        
    Example:
        >>> calculate_gravity_accuracy(75.0, 7.2)
        92.8
        
        >>> calculate_gravity_accuracy(-30.0, -2.8)
        99.2
    """
    try:
        # Normalize the -100 to 100 score to match price movement scale
        # Divide by 10 to convert sentiment scale to price change scale
        normalized_prediction = predicted_score / 10.0
        
        # Calculate absolute error between prediction and actual
        error = abs(normalized_prediction - price_change_percent)
        
        # Convert error to accuracy percentage (100% - error impact)
        # Error impact is multiplied by 10 to make it more sensitive
        accuracy = max(0, 100 - (error * 10))
        
        # Round to 2 decimal places for clean output
        return round(accuracy, 2)
        
    except (TypeError, ValueError) as e:
        logger.error(f"Error calculating gravity accuracy: {e}")
        return 0.0


def calculate_directional_accuracy(predicted_score: float, price_change_percent: float) -> bool:
    """
    Calculate if gravity model correctly predicted direction of price movement
    
    Args:
        predicted_score: Gravity-based sentiment score (-100 to +100)
        price_change_percent: Actual stock price change percentage
        
    Returns:
        True if direction was predicted correctly, False otherwise
    """
    try:
        predicted_direction = 1 if predicted_score > 0 else -1 if predicted_score < 0 else 0
        actual_direction = 1 if price_change_percent > 0 else -1 if price_change_percent < 0 else 0
        
        return predicted_direction == actual_direction
    except (TypeError, ValueError):
        return False


def get_accuracy_grade(accuracy_percentage: float) -> str:
    """
    Convert accuracy percentage to letter grade for easy interpretation
    
    Args:
        accuracy_percentage: Accuracy value (0-100)
        
    Returns:
        Letter grade string
    """
    if accuracy_percentage >= 95:
        return "A+"
    elif accuracy_percentage >= 90:
        return "A"
    elif accuracy_percentage >= 85:
        return "B+"
    elif accuracy_percentage >= 80:
        return "B"
    elif accuracy_percentage >= 75:
        return "C+"
    elif accuracy_percentage >= 70:
        return "C"
    elif accuracy_percentage >= 60:
        return "D"
    else:
        return "F"


def analyze_prediction_performance(predictions_data: List[Dict]) -> Dict:
    """
    Analyze overall performance of gravity model predictions
    
    Args:
        predictions_data: List of dictionaries with prediction results
        
    Returns:
        Performance analysis dictionary
    """
    if not predictions_data:
        return {
            'total_predictions': 0,
            'average_accuracy': 0.0,
            'directional_accuracy_rate': 0.0,
            'performance_grade': 'No Data'
        }
    
    accuracies = []
    correct_directions = 0
    
    for data in predictions_data:
        if 'gravity_accuracy' in data and data['gravity_accuracy'] is not None:
            accuracies.append(float(data['gravity_accuracy']))
            
        if 'predicted_score' in data and 'price_change_percent' in data:
            if calculate_directional_accuracy(data['predicted_score'], data['price_change_percent']):
                correct_directions += 1
    
    avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
    directional_rate = (correct_directions / len(predictions_data)) * 100 if predictions_data else 0.0
    
    return {
        'total_predictions': len(predictions_data),
        'average_accuracy': round(avg_accuracy, 2),
        'directional_accuracy_rate': round(directional_rate, 2),
        'performance_grade': get_accuracy_grade(avg_accuracy),
        'predictions_with_accuracy': len(accuracies)
    }