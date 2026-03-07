"""
Database Manager for NVIDIA Stock Prediction System
Handles all PostgreSQL database operations for market data and articles
Operates strictly on New York Time (EST/EDT) for financial accuracy
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import pytz
from typing import Dict, List, Optional, Any
from config.settings import DB_CONFIG
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DatabaseManager:
    """Manage all database operations for stock prediction system with NY timezone reference"""
    
    def __init__(self):
        """Initialize database manager with strict NY timezone operations"""
        self.config = DB_CONFIG
        
        # PRIMARY TIMEZONE REFERENCE: New York (EST/EDT)
        self.ny_tz = pytz.timezone('America/New_York')
        self.israel_tz = pytz.timezone('Asia/Jerusalem')
        
        # Print timezone validation on every initialization
        self._print_timezone_validation()
        
        logger.info("DatabaseManager initialized with NY timezone reference")
    
    def _print_timezone_validation(self):
        """Print timezone validation: [Israel Time] | [NY Time] | [Active Trading Day]"""
        now_utc = datetime.now(pytz.UTC)
        now_israel = now_utc.astimezone(self.israel_tz)
        now_ny = now_utc.astimezone(self.ny_tz)
        
        # Determine active trading day (current NY date)
        active_trading_day = now_ny.strftime('%Y-%m-%d')
        
        print(f"🌍 TIMEZONE VALIDATION:")
        print(f"   Current Israel Time: {now_israel.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"   Current Market Time: {now_ny.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"   Active Trading Day:  {active_trading_day}")
        print()
        
        logger.info(f"Timezone Validation - Israel: {now_israel} | NY: {now_ny} | Trading Day: {active_trading_day}")
    
    def get_ny_trading_date(self) -> str:
        """Get current trading date in New York timezone"""
        ny_now = datetime.now(self.ny_tz)
        return ny_now.strftime('%Y-%m-%d')
    
    def get_ny_datetime(self) -> datetime:
        """Get current datetime in New York timezone"""
        return datetime.now(self.ny_tz)
    
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
    
    def execute_sql(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute raw SQL command and return results
        
        Args:
            sql: SQL command to execute
            params: Optional parameters for the SQL command
        
        Returns:
            List of dictionaries with results (empty list for non-SELECT queries)
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            # Check if it's a SELECT query
            if sql.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                return [dict(row) for row in results]
            else:
                # For non-SELECT queries (INSERT, UPDATE, DELETE, ALTER, etc.)
                conn.commit()
                return []
        
        except Exception as e:
            logger.error(f"SQL execution failed: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
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
                        bollinger_upper = %s,
                        bollinger_lower = %s,
                        bollinger_width = %s,
                        bollinger_pctb = %s,
                        atr = %s,
                        atr_percent = %s,
                        volume_ratio = %s,
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
                    data.get('bollinger_upper'),
                    data.get('bollinger_lower'),
                    data.get('bollinger_width'),
                    data.get('bollinger_pctb'),
                    data.get('atr'),
                    data.get('atr_percent'),
                    data.get('volume_ratio'),
                    data['date']
                ))
                logger.info(f"Updated daily data for {data['date']}")
            else:
                # Insert new record
                query = """
                    INSERT INTO daily_data (
                        date, open_price, close_price, high_price, low_price, volume,
                        rsi, macd, macd_signal, moving_avg_50, moving_avg_200,
                        bollinger_upper, bollinger_lower, bollinger_width, bollinger_pctb,
                        atr, atr_percent, volume_ratio
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    data.get('moving_avg_200'),
                    data.get('bollinger_upper'),
                    data.get('bollinger_lower'),
                    data.get('bollinger_width'),
                    data.get('bollinger_pctb'),
                    data.get('atr'),
                    data.get('atr_percent'),
                    data.get('volume_ratio')
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
    
    def _run_migrations(self) -> None:
        """
        Run database migrations to ensure schema is up to date
        """
        try:
            # Check if full_content column exists in articles table
            check_column_sql = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'articles' AND column_name = 'full_content'
            """
            
            result = self.execute_sql(check_column_sql)
            
            if not result:  # Column doesn't exist, add it
                logger.info("🔧 Running migration: Adding full_content column to articles table")
                alter_sql = "ALTER TABLE articles ADD COLUMN full_content TEXT"
                self.execute_sql(alter_sql)
                logger.info("✅ Migration completed: full_content column added")
            else:
                logger.info("✅ Database schema is up to date")
            
            # Migration: Add new technical indicator columns to daily_data
            new_columns = {
                'bollinger_upper': 'NUMERIC(10,2)',
                'bollinger_lower': 'NUMERIC(10,2)',
                'bollinger_width': 'NUMERIC(6,2)',
                'bollinger_pctb': 'NUMERIC(6,4)',
                'atr': 'NUMERIC(10,2)',
                'atr_percent': 'NUMERIC(6,2)',
                'volume_ratio': 'NUMERIC(6,2)',
                'opening_gap_percent': 'NUMERIC(6,2)',
            }
            
            for col_name, col_type in new_columns.items():
                check_sql = f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'daily_data' AND column_name = '{col_name}'
                """
                exists = self.execute_sql(check_sql)
                if not exists:
                    alter_sql = f"ALTER TABLE daily_data ADD COLUMN {col_name} {col_type}"
                    self.execute_sql(alter_sql)
                    logger.info(f"🔧 Migration: Added {col_name} ({col_type}) to daily_data")
            
        except Exception as e:
            logger.warning(f"Migration warning: {str(e)}")
    
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
                    date, url, source, title, summary, full_content, sentiment_score, article_type
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """
            cursor.execute(query, (
                article['date'],
                article.get('url'),
                article.get('source'),
                article.get('title'),
                article.get('summary', ''),  # Keep snippet for backward compatibility
                article.get('full_content', ''),  # Full scraped content
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
    
    def update_next_day_opening_result(self, previous_date: str, next_day_open: float) -> bool:
        """
        Update previous day's next_day_open and calculate opening gap percentage
        
        Args:
            previous_date: Previous trading day date in YYYY-MM-DD format
            next_day_open: Today's opening price
        
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
            # Calculate opening gap percentage: (next_day_open - current_close) / current_close * 100
            opening_gap_percent = ((next_day_open - previous_close) / previous_close) * 100
            
            # Update previous day's row with opening gap data
            query = """
                UPDATE daily_data 
                SET next_day_open = %s, 
                    opening_gap_percent = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE date = %s
            """
            cursor.execute(query, (next_day_open, opening_gap_percent, previous_date))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Updated opening gap for {previous_date}: ${next_day_open:.2f} (gap: {opening_gap_percent:+.2f}%)")
            return True
            
        except Exception as e:
            logger.error(f"Error updating next day opening result: {str(e)}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    def update_next_day_result(self, previous_date: str, next_day_close: float) -> bool:
        """
        Update previous day's next_day_close and calculate close-to-close price change
        NOTE: For opening gap predictions, use update_next_day_opening_result() instead
        
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
    
    def update_sentiment_scores(self, date: str, company_sentiment: float, macro_sentiment: float, combined_sentiment: float, sentiment_range: str = None, entropy: str = None) -> bool:
        """
        Update all sentiment scores for a specific date (company, macro, and combined)
        
        Args:
            date: Date in YYYY-MM-DD format
            company_sentiment: Company-specific sentiment score
            macro_sentiment: Macro/market sentiment score
            combined_sentiment: Combined weighted sentiment score (point_score/Head)
            sentiment_range: Probability range string (Tail) e.g., "-10 to +20"
            entropy: Information dispersion level (High/Medium/Low)
        
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
                    sentiment_range = %s,
                    entropy = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE date = %s
            """
            cursor.execute(query, (company_sentiment, macro_sentiment, combined_sentiment, sentiment_range, entropy, date))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"Updated sentiment scores for {date}: Company={company_sentiment}, Macro={macro_sentiment}, Combined={combined_sentiment}, Range={sentiment_range}, Entropy={entropy}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating sentiment scores: {str(e)}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    def update_article_gravity_data(self, article_id: int, gravitational_mass: float, field_vector: float) -> bool:
        """
        Update gravitational mass and field vector for a specific article
        
        Args:
            article_id: ID of the article to update
            gravitational_mass: Informational mass weight (0-10)
            field_vector: Field vector sentiment score (-100 to +100)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
                UPDATE articles 
                SET gravitational_mass = %s,
                    sentiment_score = %s
                WHERE id = %s
            """
            cursor.execute(query, (gravitational_mass, field_vector, article_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Updated article {article_id} gravity data: Mass={gravitational_mass}, Vector={field_vector}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating article gravity data: {str(e)}")
            if conn:
                conn.rollback()
                conn.close()
            return False

    def save_batch_sentiment(self, date: str, batch_result: Dict, article_ids: List[int]) -> bool:
        """
        Save batch sentiment analysis results to database
        
        Args:
            date: Date in YYYY-MM-DD format
            batch_result: Dictionary with batch analysis results
            article_ids: List of article IDs that were analyzed
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Extract values from batch result with defaults
            point_score = float(batch_result.get('point_score', 0.0))
            sentiment_range = batch_result.get('probability_range', '0 to 0')
            entropy = batch_result.get('entropy', 'Medium')
            company_impact = float(batch_result.get('company_impact', 0.0))
            macro_impact = float(batch_result.get('macro_impact', 0.0))
            
            # Update daily_data with batch results
            query = """
                UPDATE daily_data 
                SET company_sentiment = %s,
                    macro_sentiment = %s, 
                    sentiment_score = %s,
                    sentiment_range = %s,
                    entropy = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE date = %s
            """
            cursor.execute(query, (company_impact, macro_impact, point_score, sentiment_range, entropy, date))
            
            # Update individual articles with gravity data if available
            if 'article_details' in batch_result:
                for i, article_detail in enumerate(batch_result['article_details']):
                    if i < len(article_ids):
                        article_id = article_ids[i]
                        gravitational_mass = float(article_detail.get('gravitational_mass', 1.0))
                        field_vector = float(article_detail.get('field_vector', 0.0))
                        
                        update_article_query = """
                            UPDATE articles 
                            SET gravitational_mass = %s,
                                sentiment_score = %s
                            WHERE id = %s
                        """
                        cursor.execute(update_article_query, (gravitational_mass, field_vector, article_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Saved batch sentiment for {date}: Score={point_score}, Range={sentiment_range}, Entropy={entropy}")
            logger.info(f"  Company Impact: {company_impact}, Macro Impact: {macro_impact}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving batch sentiment: {str(e)}")
            if conn:
                conn.rollback()
                conn.close()
            return False

    @staticmethod
    def calculate_range_width(sentiment_range: str) -> float:
        """
        Calculate the width of a probability range for volatility analysis
        
        Args:
            sentiment_range: Range string like "-10 to +20" or "-5 to 15"
        
        Returns:
            Range width as float (e.g., 30.0 for "-10 to +20")
        """
        if not sentiment_range or " to " not in sentiment_range:
            return 0.0
        
        try:
            parts = sentiment_range.split(" to ")
            if len(parts) != 2:
                return 0.0
            
            # Clean and parse the bounds
            lower = float(parts[0].replace("+", "").strip())
            upper = float(parts[1].replace("+", "").strip())
            
            width = upper - lower
            logger.debug(f"Range width calculation: '{sentiment_range}' -> {width}")
            return width
            
        except (ValueError, IndexError) as e:
            logger.error(f"Error calculating range width from '{sentiment_range}': {str(e)}")
            return 0.0
    
    def update_gravity_accuracy(self, date: str, gravity_accuracy: float) -> bool:
        """
        Update gravity accuracy and grade for a specific date
        
        Args:
            date: Date in YYYY-MM-DD format
            gravity_accuracy: Calculated accuracy percentage (0-100)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from utils.analysis_utils import get_accuracy_grade
            gravity_grade = get_accuracy_grade(gravity_accuracy)
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
                UPDATE daily_data 
                SET gravity_accuracy = %s,
                    gravity_grade = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE date = %s
            """
            cursor.execute(query, (gravity_accuracy, gravity_grade, date))
            
            if cursor.rowcount == 0:
                logger.warning(f"No rows updated - date {date} not found in daily_data")
                return False
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Updated gravity accuracy for {date}: {gravity_accuracy}% (Grade: {gravity_grade})")
            return True
            
        except Exception as e:
            logger.error(f"Error updating gravity accuracy: {str(e)}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    def get_predictions_for_accuracy_calculation(self, limit: int = 30) -> List[Dict]:
        """
        Get predictions that need accuracy calculation (have price_change_percent but no gravity_accuracy)
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of dictionaries with prediction data
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT date, sentiment_score, opening_gap_percent, gravity_accuracy
                FROM daily_data 
                WHERE sentiment_score IS NOT NULL 
                    AND opening_gap_percent IS NOT NULL
                    AND gravity_accuracy IS NULL
                ORDER BY date DESC
                LIMIT %s
            """
            
            cursor.execute(query, (limit,))
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error fetching predictions for accuracy calculation: {str(e)}")
            return []
    
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
            
            # Convert 'UP'/'DOWN' to numeric values
            pred_value = 1 if prediction == 'UP' else -1 if prediction == 'DOWN' else None
            if pred_value is None:
                logger.error(f"Invalid prediction value: {prediction}")
                cursor.close()
                conn.close()
                return False
            query = """
                UPDATE daily_data 
                SET prediction = %s
                WHERE date = %s
            """
            cursor.execute(query, (pred_value, date))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Saved prediction for {date}: {prediction} ({confidence:.1%})")
            return True
            
        except Exception as e:
            logger.error(f"Error saving prediction: {str(e)}")
            return False
    
    def save_opening_prediction(self, date: str, prediction: str, confidence: float) -> bool:
        """
        Save an opening prediction (GAP UP/GAP DOWN) to the database
        
        Args:
            date: Date of prediction
            prediction: 'GAP UP' or 'GAP DOWN'
            confidence: Confidence level (0-1)
        
        Returns:
            True if successful
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Convert to numeric: 1 = GAP UP, -1 = GAP DOWN
            pred_value = 1 if 'UP' in prediction else -1
            
            query = """
                UPDATE daily_data 
                SET opening_prediction = %s
                WHERE date = %s
            """
            cursor.execute(query, (pred_value, date))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Saved opening prediction for {date}: {prediction} ({confidence:.1%})")
            return True
            
        except Exception as e:
            logger.error(f"Error saving opening prediction: {str(e)}")
            return False
    
    def save_hybrid_prediction(self, date: str, gravity_score: float, confidence: str = None) -> bool:
        """
        Save hybrid prediction (gravity score) to the database
        
        Args:
            date: Date of prediction
            gravity_score: Final gravity score from hybrid analysis
            confidence: Confidence level (optional)
        
        Returns:
            True if successful
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
                UPDATE daily_data 
                SET gravity_score = %s
                WHERE date = %s
            """
            cursor.execute(query, (gravity_score, date))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Saved hybrid prediction for {date}: gravity_score={gravity_score:+.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving hybrid prediction: {str(e)}")
            return False
    
    def backfill_next_day_results(self) -> Dict[str, Any]:
        """
        Smart Temporal Integrity Patch — Backfill missing next_day_open / next_day_close.
        
        For each row in daily_data where either value is NULL:
          1. Find the FIRST valid trading day after that row's date (T+1)
          2. Fetch T+1 Open and Close from yfinance
          3. Update next_day_open, next_day_close, and price_change_percent
        
        Returns:
            Dict with counts: filled, skipped, errors
        """
        from data.market_data_fetcher import MarketDataFetcher

        stats = {"filled": 0, "skipped": 0, "errors": 0, "details": []}

        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Step 1 — Detect gaps
            cursor.execute("""
                SELECT date, close_price, next_day_open, next_day_close
                FROM daily_data
                WHERE next_day_open IS NULL OR next_day_close IS NULL
                ORDER BY date
            """)
            gap_rows = cursor.fetchall()
            cursor.close()
            conn.close()

            if not gap_rows:
                logger.info("✅ Backfill: No gaps found — all next_day fields are populated")
                return stats

            logger.info(f"🔍 Backfill: Found {len(gap_rows)} rows with missing next_day data")

            # Step 2 — Initialize fetcher once
            fetcher = MarketDataFetcher()

            for row in gap_rows:
                row_date = str(row['date'])
                close_price = float(row['close_price'])
                existing_open = row['next_day_open']
                existing_close = row['next_day_close']

                try:
                    # Step 3 — Find T+1 trading day
                    next_trading_day = fetcher.get_next_trading_session(row_date)
                    if not next_trading_day:
                        logger.warning(f"⚠️  Backfill: Could not find next trading session for {row_date}")
                        stats["skipped"] += 1
                        continue

                    # Step 4 — Fetch T+1 market data
                    t1_data = fetcher.fetch_daily_data(next_trading_day)
                    if not t1_data:
                        logger.warning(f"⚠️  Backfill: No market data for T+1 ({next_trading_day}) after {row_date}")
                        stats["skipped"] += 1
                        continue

                    t1_open = t1_data['open_price']
                    t1_close = t1_data['close_price']

                    # Use existing values if only one side is missing
                    final_open = t1_open if existing_open is None else float(existing_open)
                    final_close = t1_close if existing_close is None else float(existing_close)

                    # Calculate price_change_percent (close-to-close)
                    price_change_pct = ((final_close - close_price) / close_price) * 100

                    # Step 5 — Precision update
                    conn = self.get_connection()
                    cur = conn.cursor()
                    cur.execute("""
                        UPDATE daily_data
                        SET next_day_open = %s,
                            next_day_close = %s,
                            price_change_percent = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE date = %s
                    """, (final_open, final_close, round(price_change_pct, 4), row_date))
                    conn.commit()
                    cur.close()
                    conn.close()

                    stats["filled"] += 1
                    detail = (f"✅ {row_date} → T+1={next_trading_day}  "
                              f"Open=${final_open:.2f}  Close=${final_close:.2f}  "
                              f"Δ={price_change_pct:+.2f}%")
                    stats["details"].append(detail)
                    logger.info(detail)

                except Exception as inner_e:
                    logger.error(f"❌ Backfill error for {row_date}: {str(inner_e)}")
                    stats["errors"] += 1

            logger.info(f"📊 Backfill complete — Filled: {stats['filled']}, "
                        f"Skipped: {stats['skipped']}, Errors: {stats['errors']}")
            return stats

        except Exception as e:
            logger.error(f"❌ Backfill fatal error: {str(e)}")
            stats["errors"] += 1
            return stats

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
