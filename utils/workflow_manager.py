"""
Workflow Manager for handling weekend news and sentiment updates
Manages the logic of accumulating weekend articles and updating last trading day
"""

from datetime import datetime
from typing import Optional, List, Dict
from utils.database_manager import DatabaseManager
from utils.market_data_fetcher import MarketDataFetcher
from utils.logger import setup_logger

logger = setup_logger(__name__)


class WorkflowManager:
    """Manage daily workflow including weekend article handling"""
    
    def __init__(self):
        """Initialize workflow manager"""
        self.db = DatabaseManager()
        self.fetcher = MarketDataFetcher()
        logger.info("WorkflowManager initialized")
    
    def should_collect_market_data(self, date: Optional[str] = None) -> bool:
        """
        Determine if we should collect market data for a date
        
        Args:
            date: Date in YYYY-MM-DD format (default: today)
        
        Returns:
            True if market data should be collected, False if weekend/holiday
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        is_open = self.fetcher.is_market_open(date)
        logger.info(f"Market {'open' if is_open else 'closed'} on {date}")
        return is_open
    
    def get_last_trading_day_for_update(self) -> Optional[str]:
        """
        Get the last trading day date (the one we'll update with weekend sentiment)
        
        Returns:
            Date string or None
        """
        # Try database first
        last_day = self.db.get_last_trading_day_date()
        
        if not last_day:
            # Database empty, get from market data
            last_day = self.fetcher.get_last_trading_day()
        
        return last_day
    
    def get_date_range_for_sentiment(self, target_date: Optional[str] = None) -> tuple:
        """
        Get the date range for calculating sentiment
        
        For weekends: Returns (last_trading_day, today) to include all articles
        For trading days: Returns (today, today) for just today's articles
        
        Args:
            target_date: Date to check (default: today)
        
        Returns:
            Tuple of (start_date, end_date) for article collection
        """
        if target_date is None:
            target_date = datetime.now().strftime("%Y-%m-%d")
        
        is_trading_day = self.fetcher.is_market_open(target_date)
        
        if is_trading_day:
            # Trading day - just collect today's articles
            logger.info(f"Trading day: Collecting articles for {target_date}")
            return (target_date, target_date)
        else:
            # Weekend/Holiday - get articles since last trading day
            last_trading_day = self.get_last_trading_day_for_update()
            if not last_trading_day:
                logger.warning("Cannot determine last trading day")
                return (target_date, target_date)
            
            logger.info(f"Non-trading day: Accumulating articles from {last_trading_day} to {target_date}")
            return (last_trading_day, target_date)
    
    def process_daily_workflow(self, date: Optional[str] = None, 
                               articles: Optional[List[Dict]] = None,
                               sentiment_score: Optional[float] = None) -> Dict:
        """
        Process the daily workflow - handles both trading days and weekends
        
        Args:
            date: Date to process (default: today)
            articles: List of articles collected (optional - for testing)
            sentiment_score: Pre-calculated sentiment score (optional - for testing)
        
        Returns:
            Dictionary with workflow results
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Processing workflow for {date}")
        
        result = {
            "date": date,
            "is_trading_day": False,
            "market_data_saved": False,
            "articles_saved": 0,
            "sentiment_updated": False,
            "target_date_for_sentiment": None
        }
        
        # Check if market is open
        is_trading_day = self.should_collect_market_data(date)
        result["is_trading_day"] = is_trading_day
        
        if is_trading_day:
            # TRADING DAY: Fetch and save market data
            logger.info(f"Trading day: Fetching market data for {date}")
            market_data = self.fetcher.fetch_daily_data(date)
            
            if market_data:
                success = self.db.save_daily_data(market_data)
                result["market_data_saved"] = success
                logger.info(f"Market data saved: {success}")
            else:
                logger.warning(f"No market data available for {date}")
            
            # Save articles for today
            if articles:
                for article in articles:
                    article['date'] = date
                    self.db.save_article(article)
                result["articles_saved"] = len(articles)
            
            # Update sentiment for today
            if sentiment_score is not None:
                self.db.update_sentiment_score(date, sentiment_score)
                result["sentiment_updated"] = True
                result["target_date_for_sentiment"] = date
            
        else:
            # WEEKEND/HOLIDAY: Update last trading day's sentiment
            logger.info(f"Non-trading day: Updating last trading day with accumulated sentiment")
            
            last_trading_day = self.get_last_trading_day_for_update()
            if not last_trading_day:
                logger.error("No last trading day found - database might be empty")
                return result
            
            # Save articles with today's date
            if articles:
                for article in articles:
                    article['date'] = date
                    self.db.save_article(article)
                result["articles_saved"] = len(articles)
            
            # Update last trading day's sentiment with accumulated score
            if sentiment_score is not None:
                success = self.db.update_sentiment_score(last_trading_day, sentiment_score)
                result["sentiment_updated"] = success
                result["target_date_for_sentiment"] = last_trading_day
                logger.info(f"Updated {last_trading_day} sentiment to {sentiment_score}")
        
        return result
    
    def get_articles_for_sentiment_calculation(self, date: Optional[str] = None) -> List[Dict]:
        """
        Get all relevant articles for sentiment calculation
        
        On weekends: Gets articles from last trading day to now
        On trading days: Gets just today's articles
        
        Args:
            date: Date to check (default: today)
        
        Returns:
            List of articles to analyze
        """
        start_date, end_date = self.get_date_range_for_sentiment(date)
        articles = self.db.get_articles_since_date(start_date, end_date)
        
        logger.info(f"Retrieved {len(articles)} articles from {start_date} to {end_date}")
        return articles
    
    def get_summary(self) -> Dict:
        """
        Get workflow summary statistics
        
        Returns:
            Dictionary with summary stats
        """
        return {
            "total_trading_days": self.db.get_data_count(),
            "last_trading_day": self.db.get_last_trading_day_date(),
            "market_open_today": self.fetcher.is_market_open(),
            "latest_price": self.fetcher.get_latest_price()
        }


# ============================================
# MODULE TEST
# ============================================
if __name__ == "__main__":
    """Test the workflow manager"""
    from utils.logger import log_section_header
    
    logger = setup_logger("test_workflow")
    log_section_header(logger, "Workflow Manager Test")
    
    wf = WorkflowManager()
    
    # Test 1: Check today's workflow type
    logger.info("Test 1: Checking today's workflow...")
    is_trading = wf.should_collect_market_data()
    logger.info(f"✓ Today is {'trading day' if is_trading else 'non-trading day'}")
    
    # Test 2: Get date range for sentiment
    logger.info("\nTest 2: Getting date range for sentiment...")
    start, end = wf.get_date_range_for_sentiment()
    logger.info(f"✓ Date range: {start} to {end}")
    
    # Test 3: Get summary
    logger.info("\nTest 3: Getting workflow summary...")
    summary = wf.get_summary()
    for key, value in summary.items():
        logger.info(f"  {key}: {value}")
    
    logger.info("\n✓ Workflow manager tests passed!")
