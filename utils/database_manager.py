"""
Database Manager for NVIDIA Stock Prediction System
Handles all PostgreSQL database operations for market data and articles
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, List, Optional, Any
from config.settings import DB_CONFIG
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DatabaseManager:
    """Manage all database operations for stock prediction system"""
    
    def __init__(self):
        """Initialize database manager with connection config"""
        self.config = DB_CONFIG
        logger.info("DatabaseManager initialized")
    
    def get_connection(self):
        """
        Create and return a database connection
        
        Returns:
            psycopg2 connection object
        """
        try:
            conn = psycopg2.connect(**self.config)
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise
    
    def save_daily_data(self, data: Dict[str, Any]) -> bool:
        """
        Save or update daily stock data
        
        Args:
            data: Dictionary containing daily stock data
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if date already exists
            cursor.execute(
                "SELECT id FROM daily_data WHERE date = %s",
                (data['date'],)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                query = """
                    UPDATE daily_data SET
                        open_price = %s,
                        close_price = %s,
                        high_price = %s,
                        low_price = %s,
                        volume = %s,
                        rsi = %s,
                        macd = %s,
                        macd_signal = %s,
                        moving_avg_50 = %s,
                        moving_avg_200 = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE date = %s
                """
                cursor.execute(query, (
                    data.get('open_price'),
                    data.get('close_price'),
                    data.get('high_price'),
                    data.get('low_price'),
                    data.get('volume'),
                    data.get('rsi'),
                    data.get('macd'),
                    data.get('macd_signal'),
                    data.get('moving_avg_50'),
                    data.get('moving_avg_200'),
                    data['date']
                ))
                logger.info(f"Updated daily data for {data['date']}")
            else:
                # Insert new record
                query = """
                    INSERT INTO daily_data (
                        date, open_price, close_price, high_price, low_price, volume,
                        rsi, macd, macd_signal, moving_avg_50, moving_avg_200
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    data['date'],
                    data.get('open_price'),
                    data.get('close_price'),
                    data.get('high_price'),
                    data.get('low_price'),
                    data.get('volume'),
                    data.get('rsi'),
                    data.get('macd'),
                    data.get('macd_signal'),
                    data.get('moving_avg_50'),
                    data.get('moving_avg_200')
                ))
                logger.info(f"Inserted daily data for {data['date']}")
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error saving daily data: {str(e)}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    def save_article(self, article: Dict[str, Any]) -> bool:
        """
        Save a news article to database
        
        Args:
            article: Dictionary containing article data
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO articles (
                    date, url, source, title, summary, sentiment_score, article_type
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """
            cursor.execute(query, (
                article['date'],
                article.get('url'),
                article.get('source'),
                article.get('title'),
                article.get('summary'),
                article.get('sentiment_score'),
                article.get('article_type', 'company')  # Default to 'company' for backward compatibility
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.debug(f"Saved article: {article.get('title', 'No title')[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error saving article: {str(e)}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    def update_next_day_result(self, previous_date: str, next_day_close: float) -> bool:
        """
        Update previous day's next_day_close and calculate price change
        
        Args:
            previous_date: Previous trading day date in YYYY-MM-DD format
            next_day_close: Today's closing price
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get previous day's close price
            cursor.execute("SELECT close_price FROM daily_data WHERE date = %s", (previous_date,))
            result = cursor.fetchone()
            
            if not result:
                logger.warning(f"No data found for previous date {previous_date}")
                cursor.close()
                conn.close()
                return False
            
            previous_close = float(result[0])
            price_change_percent = ((next_day_close - previous_close) / previous_close) * 100
            
            # Update previous day's row
            query = """
                UPDATE daily_data 
                SET next_day_close = %s, 
                    price_change_percent = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE date = %s
            """
            cursor.execute(query, (next_day_close, price_change_percent, previous_date))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Updated next day result for {previous_date}: ${next_day_close:.2f} ({price_change_percent:+.2f}%)")
            return True
            
        except Exception as e:
            logger.error(f"Error updating next day result: {str(e)}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    def update_sentiment_score(self, date: str, sentiment_score: float) -> bool:
        """
        Update combined sentiment score for a specific date
        
        Args:
            date: Date in YYYY-MM-DD format
            sentiment_score: Aggregated sentiment score (combined company + macro)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
                UPDATE daily_data 
                SET sentiment_score = %s, updated_at = CURRENT_TIMESTAMP
                WHERE date = %s
            """
            cursor.execute(query, (sentiment_score, date))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"Updated sentiment score for {date}: {sentiment_score}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating sentiment score: {str(e)}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    def update_sentiment_scores(self, date: str, company_sentiment: float, macro_sentiment: float, combined_sentiment: float) -> bool:
        """
        Update all sentiment scores for a specific date (company, macro, and combined)
        
        Args:
            date: Date in YYYY-MM-DD format
            company_sentiment: Company-specific sentiment score
            macro_sentiment: Macro/market sentiment score
            combined_sentiment: Combined weighted sentiment score
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
                UPDATE daily_data 
                SET company_sentiment = %s, 
                    macro_sentiment = %s,
                    sentiment_score = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE date = %s
            """
            cursor.execute(query, (company_sentiment, macro_sentiment, combined_sentiment, date))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"Updated sentiment scores for {date}: Company={company_sentiment}, Macro={macro_sentiment}, Combined={combined_sentiment}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating sentiment scores: {str(e)}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    def get_daily_data(self, date: str) -> Optional[Dict]:
        """
        Retrieve daily data for a specific date
        
        Args:
            date: Date in YYYY-MM-DD format
        
        Returns:
            Dictionary with daily data or None if not found
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = "SELECT * FROM daily_data WHERE date = %s"
            cursor.execute(query, (date,))
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                return dict(result)
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving daily data: {str(e)}")
            return None
    
    def get_historical_data(self, days: int = 30) -> List[Dict]:
        """
        Retrieve historical data for the last N days
        
        Args:
            days: Number of days to retrieve
        
        Returns:
            List of dictionaries with daily data
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT * FROM daily_data 
                ORDER BY date DESC 
                LIMIT %s
            """
            cursor.execute(query, (days,))
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error retrieving historical data: {str(e)}")
            return []
    
    def get_articles_for_date(self, date: str) -> List[Dict]:
        """
        Retrieve all articles for a specific date
        
        Args:
            date: Date in YYYY-MM-DD format
        
        Returns:
            List of article dictionaries
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = "SELECT * FROM articles WHERE date = %s ORDER BY created_at DESC"
            cursor.execute(query, (date,))
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error retrieving articles: {str(e)}")
            return []
    
    def get_articles_before_date(self, date: str) -> List[Dict]:
        """
        Retrieve all articles published before a specific date
        Useful for finding orphaned weekend articles
        
        Args:
            date: Cutoff date in YYYY-MM-DD format
        
        Returns:
            List of article dictionaries
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = "SELECT * FROM articles WHERE date < %s ORDER BY date DESC"
            cursor.execute(query, (date,))
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error retrieving articles before date: {str(e)}")
            return []
    
    def date_exists(self, date: str) -> bool:
        """
        Check if data exists for a specific date
        
        Args:
            date: Date in YYYY-MM-DD format
        
        Returns:
            True if data exists, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = "SELECT EXISTS(SELECT 1 FROM daily_data WHERE date = %s)"
            cursor.execute(query, (date,))
            exists = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return exists
            
        except Exception as e:
            logger.error(f"Error checking date existence: {str(e)}")
            return False
    
    def get_data_count(self) -> int:
        """
        Get total count of days in database
        
        Returns:
            Number of days stored in database
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = "SELECT COUNT(*) FROM daily_data"
            cursor.execute(query)
            count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return count
            
        except Exception as e:
            logger.error(f"Error getting data count: {str(e)}")
            return 0
    
    def get_last_trading_day_date(self) -> Optional[str]:
        """
        Get the most recent trading day date from database
        
        Returns:
            Date string in YYYY-MM-DD format or None if no data
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = "SELECT date FROM daily_data ORDER BY date DESC LIMIT 1"
            cursor.execute(query)
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                return result[0].strftime("%Y-%m-%d")
            return None
            
        except Exception as e:
            logger.error(f"Error getting last trading day: {str(e)}")
            return None
    
    def get_previous_trading_day(self, current_date: str) -> Optional[str]:
        """
        Get the trading day immediately before the given date
        
        Args:
            current_date: Current date in YYYY-MM-DD format
        
        Returns:
            Previous trading day date string or None if no previous data
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = "SELECT date FROM daily_data WHERE date < %s ORDER BY date DESC LIMIT 1"
            cursor.execute(query, (current_date,))
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                return result[0].strftime("%Y-%m-%d")
            return None
            
        except Exception as e:
            logger.error(f"Error getting previous trading day: {str(e)}")
            return None
    
    def get_articles_since_date(self, start_date: str, end_date: Optional[str] = None) -> List[Dict]:
        """
        Get all articles from start_date to end_date (inclusive)
        Useful for accumulating weekend articles
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (default: today)
        
        Returns:
            List of article dictionaries
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            if end_date is None:
                from datetime import datetime
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            query = """
                SELECT * FROM articles 
                WHERE date >= %s AND date <= %s 
                ORDER BY date ASC, created_at ASC
            """
            cursor.execute(query, (start_date, end_date))
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting articles since date: {str(e)}")
            return []
    
    def update_last_trading_day_sentiment(self, sentiment_score: float) -> bool:
        """
        Update the sentiment score for the last trading day
        Used when weekend articles are collected
        
        Args:
            sentiment_score: Updated sentiment score (including weekend news)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            last_day = self.get_last_trading_day_date()
            if not last_day:
                logger.warning("No trading days found in database")
                return False
            
            return self.update_sentiment_score(last_day, sentiment_score)
            
        except Exception as e:
            logger.error(f"Error updating last trading day sentiment: {str(e)}")
            return False
    
    def get_articles_count_for_date_range(self, start_date: str, end_date: str) -> int:
        """
        Get count of articles in a date range
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        
        Returns:
            Number of articles in range
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT COUNT(*) FROM articles 
                WHERE date >= %s AND date <= %s
            """
            cursor.execute(query, (start_date, end_date))
            count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return count
            
        except Exception as e:
            logger.error(f"Error getting articles count: {str(e)}")
            return 0

    def get_all_daily_data(self) -> List[Dict]:
        """
        Get all daily data records for model training
        
        Returns:
            List of all daily data records
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT * FROM daily_data 
                ORDER BY date ASC
            """
            cursor.execute(query)
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting all daily data: {str(e)}")
            return []
    
    def get_latest_daily_data(self) -> Optional[Dict]:
        """
        Get the most recent daily data record
        
        Returns:
            Most recent daily data or None
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT * FROM daily_data 
                ORDER BY date DESC 
                LIMIT 1
            """
            cursor.execute(query)
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Error getting latest daily data: {str(e)}")
            return None
    
    def get_average_volume(self, days: int = 20) -> float:
        """
        Get average volume over recent days
        
        Args:
            days: Number of days to average
        
        Returns:
            Average volume
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT AVG(volume) FROM (
                    SELECT volume FROM daily_data 
                    ORDER BY date DESC 
                    LIMIT %s
                ) AS recent
            """
            cursor.execute(query, (days,))
            result = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return float(result) if result else 0.0
            
        except Exception as e:
            logger.error(f"Error getting average volume: {str(e)}")
            return 0.0
    
    def save_prediction(self, date: str, prediction: str, confidence: float) -> bool:
        """
        Save a prediction to the database
        
        Args:
            date: Date of prediction
            prediction: 'UP' or 'DOWN'
            confidence: Confidence level (0-1)
        
        Returns:
            True if successful
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Update the daily_data row with prediction
            query = """
                UPDATE daily_data 
                SET prediction = %s
                WHERE date = %s
            """
            cursor.execute(query, (prediction, date))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Saved prediction for {date}: {prediction} ({confidence:.1%})")
            return True
            
        except Exception as e:
            logger.error(f"Error saving prediction: {str(e)}")
            return False
    
    def get_predictions_with_results(self, days: int = 30) -> List[Dict]:
        """
        Get predictions that have actual results for evaluation
        
        Args:
            days: Number of days to look back
        
        Returns:
            List of predictions with actual results
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT 
                    date,
                    prediction,
                    close_price,
                    next_day_close,
                    CASE 
                        WHEN next_day_close > close_price THEN 'UP'
                        ELSE 'DOWN'
                    END as actual_direction
                FROM daily_data 
                WHERE prediction IS NOT NULL 
                AND next_day_close IS NOT NULL
                ORDER BY date DESC 
                LIMIT %s
            """
            cursor.execute(query, (days,))
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting predictions: {str(e)}")
            return []
