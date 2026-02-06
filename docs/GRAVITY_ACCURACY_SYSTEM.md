# Gravity Accuracy Calibration System

## Overview
The Gravity Accuracy Calibration System measures the effectiveness of your "Informational Gravity" model by calculating the 'Physical Match' between sentiment theory and market reality.

## Components

### 1. Utility Function: `calculate_gravity_accuracy()`
**Location:** `utils/analysis_utils.py`

```python
def calculate_gravity_accuracy(predicted_score: float, price_change_percent: float) -> float:
    """
    Calculate accuracy of the Informational Gravity model prediction
    
    Args:
        predicted_score: Gravity-based sentiment score (-100 to +100)
        price_change_percent: Actual stock price change percentage
        
    Returns:
        Accuracy percentage (0-100) representing 'Physical Match'
    """
```

**Formula:**
- Normalizes -100 to +100 score to price movement scale (divide by 10)
- Calculates absolute error between prediction and actual
- Converts to accuracy: `max(0, 100 - (error * 10))`

### 2. Database Integration
**New Column:** `gravity_accuracy NUMERIC(6,2)` in `daily_data` table

**Methods:**
- `update_gravity_accuracy(date, accuracy)` - Store calculated accuracy
- `get_predictions_for_accuracy_calculation()` - Find predictions needing calibration

### 3. Post-Market Workflow
**Location:** `main.py` - `run_post_market_calibration()`

**Process:**
1. Fetches actual price movements for previous predictions
2. Calculates gravity model accuracy using `calculate_gravity_accuracy()`
3. Updates database with accuracy metrics
4. Logs 'Physical Match' results with performance grades

### 4. Command Line Interface
```bash
python main.py --calibrate
```

## Usage Examples

### Basic Accuracy Calculation
```python
from utils.analysis_utils import calculate_gravity_accuracy

# Example: Good prediction
accuracy = calculate_gravity_accuracy(75.0, 7.2)  # 97.0% accuracy (A+)

# Example: Poor prediction  
accuracy = calculate_gravity_accuracy(72.5, -1.33)  # 14.2% accuracy (F)
```

### Real Market Data Integration
```python
from utils.market_data_fetcher import MarketDataFetcher
from utils.analysis_utils import calculate_gravity_accuracy

fetcher = MarketDataFetcher()
price_change = fetcher.get_price_change_percent("2026-02-04", "2026-02-05")
# Returns: -1.33%

# If you had predicted +65.0 for Feb 4:
accuracy = calculate_gravity_accuracy(65.0, -1.33)
# Returns: 21.7% accuracy (F grade)
```

### Post-Market Calibration Workflow
```python
# Automatically runs after market close
python main.py --calibrate

# Output example:
# 🎯 Physical Match: 97.0% (Grade: A+)
# 📊 Analysis:
#    Normalized Prediction: +7.5%
#    Prediction Error: 0.3%
#    Theory-Reality Match: 97.0%
# ✅ Excellent gravity model performance!
```

## Performance Grading System

| Accuracy Range | Grade | Performance Level |
|---------------|-------|------------------|
| 95-100%       | A+    | Excellent        |
| 90-94%        | A     | Excellent        |
| 85-89%        | B+    | Good             |
| 80-84%        | B     | Good             |
| 75-79%        | C+    | Moderate         |
| 70-74%        | C     | Moderate         |
| 60-69%        | D     | Poor             |
| 0-59%         | F     | Very Poor        |

## Database Schema

```sql
-- Added to daily_data table
ALTER TABLE daily_data 
ADD COLUMN gravity_accuracy NUMERIC(6,2);

COMMENT ON COLUMN daily_data.gravity_accuracy IS 
'Accuracy of Informational Gravity model prediction vs actual price movement (0-100%)';
```

## Workflow Integration

1. **Daily Prediction:** Your gravity model generates sentiment_score (Head)
2. **Market Close:** Actual price_change_percent becomes available  
3. **Post-Market Calibration:** Run `python main.py --calibrate`
4. **Accuracy Calculation:** System calculates 'Physical Match' percentage
5. **Database Storage:** Results stored in `gravity_accuracy` column
6. **Performance Analysis:** Grade assigned and logged

## Key Benefits

- **Scientific Validation:** Measure theory vs reality match
- **Performance Tracking:** Historical accuracy trends
- **Model Optimization:** Identify when calibration needed
- **Confidence Assessment:** Grade-based reliability indicators
- **Automated Workflow:** Post-market accuracy calculation

## Example Calibration Session

```
GRAVITY MODEL CALIBRATION SUMMARY
=====================================
Predictions Calibrated: 3
Average Physical Match: 87.2%
Overall Performance Grade: B+
Informational Gravity Effectiveness: 87.2%

🏆 Outstanding gravity model accuracy!
```

Your Informational Gravity model can now scientifically validate its ability to predict stock price movements!