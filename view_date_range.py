#!/usr/bin/env python3
"""
Data Viewer for Date Range
Display complete data for specified date range including market data, articles, sentiment, and predictions
"""

import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.database_manager import DatabaseManager
from utils.logger import setup_logger

# Load environment
load_dotenv()
logger = setup_logger(__name__)

class DateRangeViewer:
    """Comprehensive data viewer for date ranges"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def view_date_range(self, start_date: str, end_date: str):
        """
        Display all data for the specified date range
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        """
        print("="*80)
        print("🌊 NVIDIA INFORMATIONAL GRAVITY ENGINE - DATA VIEWER")
        print("="*80)
        print(f"📅 Date Range: {start_date} to {end_date}")
        print("="*80)
        
        # Parse dates
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            current_date = start_dt
            while current_date <= end_dt:
                date_str = current_date.strftime("%Y-%m-%d")
                self._display_daily_data(date_str)
                current_date += timedelta(days=1)
                
        except Exception as e:
            print(f"❌ Error processing date range: {e}")
    
    def _display_daily_data(self, date: str):
        """Display all data for a specific date"""
        print(f"\n📊 DATE: {date}")
        print("-" * 60)
        
        # Get market data
        market_data = self._get_market_data(date)
        if market_data:
            self._display_market_data(market_data)
        else:
            print("📈 Market Data: No data available")
        
        # Get articles
        articles = self._get_articles(date)
        if articles:
            self._display_articles(articles)
        else:
            print("📰 Articles: No articles found")
        
        # Get sentiment and prediction
        sentiment_data = self._get_sentiment_data(date)
        if sentiment_data:
            self._display_sentiment_data(sentiment_data)
        
        # Get prediction data from daily_data
        prediction_data = self._get_prediction_data(date)
        if prediction_data:
            self._display_prediction_data(prediction_data)
        
        # Get hybrid prediction data  
        hybrid_data = self._get_hybrid_data(date)
        if hybrid_data:
            self._display_hybrid_data(hybrid_data)
        
        # Get recent predictions (ML/Hybrid)
        recent_predictions = self._get_recent_predictions(date)
        if recent_predictions:
            self._display_recent_predictions(recent_predictions)
        
        print()
    
    def _get_market_data(self, date: str):
        """Get market data for date"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT date, open_price, high_price, low_price, close_price, 
                               volume, rsi, macd, price_change_percent,
                               moving_avg_50, next_day_open, prediction, prediction_accuracy
                        FROM daily_data 
                        WHERE date = %s
                    """, (date,))
                    return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return None
    
    def _get_articles(self, date: str):
        """Get articles for date"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT title, url, sentiment_score, source, article_type,
                               created_at, summary
                        FROM articles 
                        WHERE date = %s
                        ORDER BY sentiment_score DESC
                    """, (date,))
                    return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting articles: {e}")
            return []
    
    def _get_sentiment_data(self, date: str):
        """Get sentiment data for date"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT sentiment_score, company_sentiment, macro_sentiment,
                               sentiment_range, entropy, macd_signal, moving_avg_200
                        FROM daily_data 
                        WHERE date = %s
                    """, (date,))
                    return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error getting sentiment data: {e}")
            return None
    
    def _get_prediction_data(self, date: str):
        """Get prediction data from daily_data table"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT prediction, prediction_accuracy, 
                               gravity_score, gravity_accuracy, gravity_grade
                        FROM daily_data 
                        WHERE date = %s
                    """, (date,))
                    return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error getting prediction data: {e}")
            return None
    
    def _display_market_data(self, data):
        """Display market data"""
        if not data:
            return
            
        print("📈 MARKET DATA:")
        print(f"   Open: ${float(data[1]):.2f}")
        print(f"   High: ${float(data[2]):.2f}")
        print(f"   Low: ${float(data[3]):.2f}")
        print(f"   Close: ${float(data[4]):.2f}")
        print(f"   Volume: {int(data[5]):,}")
        
        if data[6]:  # RSI
            print(f"   RSI: {float(data[6]):.2f}")
        if data[7]:  # MACD
            print(f"   MACD: {float(data[7]):.2f}")
        if data[8]:  # Price change %
            print(f"   Change: {float(data[8]):.2f}%")
        if data[9]:  # Moving avg 50
            print(f"   MA50: ${float(data[9]):.2f}")
        if data[10]:  # Next day open
            print(f"   Next Day Open: ${float(data[10]):.2f}")
        if data[11]:  # Prediction
            prediction_val = "UP" if float(data[11]) > 0 else "DOWN" if float(data[11]) < 0 else "NEUTRAL"
            print(f"   ML Prediction: {prediction_val}")
        if data[12]:  # Prediction accuracy
            print(f"   Prediction Accuracy: {float(data[12]):.1f}%")
    
    def _display_articles(self, articles):
        """Display articles"""
        print(f"📰 ARTICLES ({len(articles)} found):")
        
        company_articles = [a for a in articles if a[4] == 'company']
        macro_articles = [a for a in articles if a[4] == 'macro']
        
        if company_articles:
            print(f"   🏢 Company Articles ({len(company_articles)}):")
            for article in company_articles:
                sentiment = float(article[2]) if article[2] else 0
                print(f"     • [{article[3]}] {article[0][:60]}...")
                print(f"       Sentiment: {sentiment:+.2f} | {article[1]}")
        
        if macro_articles:
            print(f"   🌍 Macro Articles ({len(macro_articles)}):")
            for article in macro_articles:
                sentiment = float(article[2]) if article[2] else 0
                print(f"     • [{article[3]}] {article[0][:60]}...")
                print(f"       Sentiment: {sentiment:+.2f} | {article[1]}")
    
    def _display_sentiment_data(self, data):
        """Display sentiment analysis data"""
        if not data or not data[0]:
            print("🎯 SENTIMENT: No sentiment data available")
            return
            
        print("🎯 SENTIMENT ANALYSIS:")
        print(f"   Combined Score: {float(data[0]):.2f}")
        
        if data[1]:  # Company sentiment
            print(f"   Company Sentiment: {float(data[1]):.2f}")
        if data[2]:  # Macro sentiment
            print(f"   Macro Sentiment: {float(data[2]):.2f}")
        if data[3]:  # Sentiment range
            print(f"   Range: {data[3]}")
        if data[4]:  # Entropy
            print(f"   Entropy: {data[4]}")
        if data[5]:  # MACD Signal
            print(f"   MACD Signal: {float(data[5]):.2f}")
        if data[6]:  # Moving avg 200
            print(f"   MA200: ${float(data[6]):.2f}")
    
    def _display_prediction_data(self, data):
        """Display prediction data"""
        if not data:
            print("🔮 PREDICTION: No prediction available")
            return
            
        print("🔮 PREDICTION:")
        if data[0]:  # Prediction value
            prediction_val = "UP" if float(data[0]) > 0 else "DOWN" if float(data[0]) < 0 else "NEUTRAL"
            print(f"   Direction: {prediction_val}")
            
        if data[1]:  # Prediction accuracy
            print(f"   Accuracy: {float(data[1]):.1f}%")
        if data[2]:  # Gravity score
            print(f"   Gravity Score: {float(data[2]):.2f}")
        if data[3]:  # Gravity accuracy
            print(f"   Gravity Accuracy: {float(data[3]):.1f}%")
        if data[4]:  # Gravity grade
            print(f"   Gravity Grade: {data[4]}")
    
    def _get_recent_predictions(self, date: str):
        """Get recent predictions (ML/Hybrid) for date"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT prediction, prediction_accuracy, sentiment_score,
                               close_price, next_day_close
                        FROM recent_predictions 
                        WHERE date = %s
                        ORDER BY close_price DESC
                    """, (date,))
                    return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting recent predictions: {e}")
            return []
    
    def _display_recent_predictions(self, predictions):
        """Display recent predictions (ML/Hybrid)"""
        print("\n" + "-" * 60)
        print("ML PREDICTION (VALIDATION)")
        print("-" * 60)
        
        for pred in predictions:
            prediction = pred[0]
            accuracy = pred[1]
            sentiment = pred[2]
            close_price = pred[3]
            next_day_close = pred[4]
            
            if prediction is not None:
                if float(prediction) > 0:
                    direction = "📈 ML PREDICTION: UP"
                elif float(prediction) < 0:
                    direction = "📉 ML PREDICTION: DOWN"
                else:
                    direction = "⚪ ML PREDICTION: NEUTRAL"
                    
                print(f"\n  {direction}")
                print(f"  Prediction Score: {float(prediction):+.2f}")
                if accuracy:
                    print(f"  Confidence: {float(accuracy):.1f}%")
                if close_price and next_day_close:
                    actual_change = ((float(next_day_close) - float(close_price)) / float(close_price)) * 100
                    print(f"  Actual: {actual_change:+.1f}%")
            break  # Only show first prediction
    def _get_hybrid_data(self, date: str):
        """Get hybrid prediction data for date"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT gravity_score, gravity_accuracy, gravity_grade,
                               sentiment_score, company_sentiment, macro_sentiment,
                               rsi, macd
                        FROM daily_data 
                        WHERE date = %s
                    """, (date,))
                    return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error getting hybrid data: {e}")
            return None
    
    def _display_hybrid_data(self, data):
        """Display hybrid prediction data"""
        if not data or not data[0]:
            return
            
        print("\n" + "-" * 60)
        print("HYBRID PREDICTION (DYNAMIC STRATEGY)")
        print("-" * 60)
        
        gravity_score = float(data[0]) if data[0] else 0
        gravity_accuracy = float(data[1]) if data[1] else 0
        gravity_grade = data[2] if data[2] else "N/A"
        sentiment_score = float(data[3]) if data[3] else 0
        company_sentiment = float(data[4]) if data[4] else 0 
        macro_sentiment = float(data[5]) if data[5] else 0
        rsi = float(data[6]) if data[6] else 50
        macd = float(data[7]) if data[7] else 0
        
        # Determine signal and alignment based on gravity score
        if gravity_score > 2:
            signal = "📈 HYBRID SIGNAL: Strong BUY signal"
            alignment = "(Strong Alignment)"
        elif gravity_score > 0:
            signal = "📈 HYBRID SIGNAL: Moderate BUY signal"
            alignment = "(Weak Alignment)" if gravity_score < 1 else "(Moderate Alignment)"
        elif gravity_score < -2:
            signal = "📉 HYBRID SIGNAL: Strong SELL signal"
            alignment = "(Strong Alignment)"
        elif gravity_score < 0:
            signal = "📉 HYBRID SIGNAL: Moderate SELL signal"
            alignment = "(Weak Alignment)" if gravity_score > -1 else "(Moderate Alignment)"
        else:
            signal = "⚪ HYBRID SIGNAL: NEUTRAL signal"
            alignment = "(No Alignment)"
        
        # Determine confidence based on gravity accuracy
        if gravity_accuracy >= 70:
            confidence = "High"
        elif gravity_accuracy >= 50:
            confidence = "Medium"
        else:
            confidence = "Low"
        
        # Calculate dynamic strategy weights 
        total_signals = abs(sentiment_score) + abs(rsi - 50) + abs(macd)
        if total_signals > 0:
            sentiment_weight = min(80, max(20, abs(sentiment_score) / total_signals * 100))
            technical_weight = 100 - sentiment_weight
        else:
            sentiment_weight = 20  # Default like in example
            technical_weight = 80
            
        print(f"\n  {signal} {alignment}")
        print(f"  Final Gravity: {gravity_score:+.2f}")
        print(f"  Confidence: {confidence}")
        print(f"  Strategy: Sentiment {sentiment_weight:.0f}% | Technical {technical_weight:.0f}%")


def main():
    """Main entry point"""
    try:
        viewer = DateRangeViewer()
        
        # View data for February 8-11, 2026 as requested
        start_date = "2026-02-08"
        end_date = "2026-02-11"
        
        viewer.view_date_range(start_date, end_date)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()