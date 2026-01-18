"""
Orchestrator Agent
Coordinates all agents and manages the daily workflow
"""

from datetime import datetime
from typing import Dict, Optional, List
from agents.base_agent import BaseAgent
from agents.news_agent import NewsAgent
from agents.sentiment_agent import SentimentAgent
from agents.prediction_agent import PredictionAgent
from utils.market_data_fetcher import MarketDataFetcher
from utils.database_manager import DatabaseManager
from utils.workflow_manager import WorkflowManager
from config.settings import MAX_NEWS_ARTICLES
from utils.logger import setup_logger, log_section_header

logger = setup_logger(__name__)


class OrchestratorAgent(BaseAgent):
    """Master agent that coordinates the entire daily workflow"""
    
    def __init__(self):
        """Initialize Orchestrator with all sub-agents and utilities"""
        super().__init__("OrchestratorAgent", temperature=0.5)
        
        # Initialize all components
        self.news_agent = NewsAgent()
        self.sentiment_agent = SentimentAgent()
        self.prediction_agent = PredictionAgent()
        self.market_fetcher = MarketDataFetcher()
        self.db = DatabaseManager()
        self.workflow = WorkflowManager()
        
        logger.info("OrchestratorAgent initialized with all components")
    
    
    def run_daily_workflow(self, date: Optional[str] = None, dry_run: bool = False) -> Dict:
        """
        Execute the complete daily workflow
        
        NEW LOGIC: Always uses last available trading day from Yahoo Finance.
        This ensures we always have data regardless of weekends/holidays/timezone.
        
        Args:
            date: Date to process (ignored - always uses last trading day)
            dry_run: If True, don't save to database (for testing)
        
        Returns:
            Dictionary with workflow results
        """
        # ALWAYS get the last trading day with actual data from Yahoo
        last_trading_day = self.market_fetcher.get_last_trading_day()
        
        if not last_trading_day:
            logger.error("Cannot determine last trading day from Yahoo Finance")
            return {
                "date": date,
                "success": False,
                "errors": ["Cannot get last trading day from Yahoo Finance"]
            }
        
        # Get today's date in NY timezone for news collection
        from zoneinfo import ZoneInfo
        ny_today = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
        
        log_section_header(logger, f"Daily Workflow")
        
        result = {
            "date": last_trading_day,
            "ny_today": ny_today,
            "success": False,
            "is_trading_day": True,  # We're always working with a trading day's data
            "market_data_collected": False,
            "market_data_existed": False,
            "articles_collected": 0,
            "sentiment_score": 0.0,
            "sentiment_confidence": "Low",
            "errors": []
        }
        
        try:
            logger.info(f"{'='*60}")
            logger.info(f"Last Trading Day: {last_trading_day}")
            logger.info(f"NY Today: {ny_today}")
            logger.info(f"{'='*60}")
            
            # Step 1: Check if market data already exists in database
            existing_data = self.db.get_daily_data(last_trading_day)
            
            if existing_data:
                logger.info(f"\n📊 STEP 1: Market Data")
                logger.info("-" * 60)
                logger.info(f"✓ Market data for {last_trading_day} already in database")
                logger.info(f"  Close: ${float(existing_data['close_price']):.2f}")
                logger.info(f"  (Skipping - no changes needed)")
                result["market_data_collected"] = True
                result["market_data_existed"] = True
            else:
                # Fetch and save market data
                market_data = self._collect_market_data(last_trading_day, dry_run)
                result["market_data_collected"] = market_data is not None
            
            # Step 2: Collect news articles (company + macro) for today
            company_articles, macro_articles = self._collect_news_articles(ny_today)
            result["articles_collected"] = len(company_articles) + len(macro_articles)
            
            if not company_articles and not macro_articles:
                logger.warning("No new articles collected - sentiment analysis skipped")
                result["errors"].append("No articles found")
            else:
                # Step 3: Analyze sentiment (separate company and macro)
                sentiment_result = self._analyze_sentiment(company_articles, macro_articles)
                result["company_sentiment"] = sentiment_result["company_sentiment"]
                result["macro_sentiment"] = sentiment_result["macro_sentiment"]
                result["sentiment_score"] = sentiment_result["combined_score"]
                result["sentiment_confidence"] = sentiment_result["combined_confidence"]
                result["company_factors"] = sentiment_result.get("company_factors", "")
                result["macro_factors"] = sentiment_result.get("macro_factors", "")
                
                # Step 4: Save articles to database (linked to last trading day)
                if not dry_run:
                    self._save_articles(company_articles, macro_articles, last_trading_day)
                
                # Step 5: Update sentiment for last trading day
                if not dry_run:
                    self._update_sentiment_simple(last_trading_day, sentiment_result)
            
            # Step 6: Make prediction (if enough data)
            prediction_result = self._make_prediction()
            result["prediction"] = prediction_result.get("prediction")
            result["prediction_confidence"] = prediction_result.get("confidence", 0.0)
            result["can_predict"] = prediction_result.get("can_predict", False)
            result["prediction_message"] = prediction_result.get("message", "")
            
            result["success"] = True
            logger.info(f"\n{'='*60}")
            logger.info(f"✓ Workflow completed successfully")
            logger.info(f"  Market data: {last_trading_day}")
            logger.info(f"  News collected: {ny_today}")
            logger.info(f"{'='*60}")
            
        except Exception as e:
            logger.error(f"Workflow failed: {str(e)}")
            result["errors"].append(str(e))
            result["success"] = False
        
        return result
    
    def _collect_market_data(self, date: str, dry_run: bool) -> Optional[Dict]:
        """
        Collect and save market data
        
        Args:
            date: Target date
            dry_run: If True, don't save to database
        
        Returns:
            Market data dictionary or None
        """
        logger.info("\n📊 STEP 1: Collecting Market Data")
        logger.info("-" * 60)
        
        try:
            # Fetch market data
            market_data = self.market_fetcher.fetch_daily_data(date)
            
            if not market_data:
                logger.error(f"Failed to fetch market data for {date}")
                return None
            
            logger.info(f"✓ Fetched market data:")
            logger.info(f"  Close: ${market_data['close_price']:.2f}")
            logger.info(f"  Volume: {market_data['volume']:,}")
            logger.info(f"  RSI: {market_data.get('rsi', 'N/A')}")
            
            # Save to database
            if not dry_run:
                success = self.db.save_daily_data(market_data)
                if success:
                    logger.info("✓ Market data saved to database")
                    
                    # Update previous day's next_day_close
                    previous_day = self.db.get_previous_trading_day(date)
                    if previous_day:
                        self.db.update_next_day_result(previous_day, market_data['close_price'])
                    
                else:
                    logger.error("Failed to save market data to database")
            else:
                logger.info("✓ Market data ready (dry run - not saved)")
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error collecting market data: {str(e)}")
            return None
    
    def _collect_news_articles(self, date: str) -> tuple[List[Dict], List[Dict]]:
        """
        Collect company and macro news articles
        
        Args:
            date: Target date
        
        Returns:
            Tuple of (company_articles, macro_articles)
        """
        logger.info("\n📰 STEP 2: Collecting News Articles")
        logger.info("-" * 60)
        
        try:
            # Collect company-specific NVIDIA news
            company_articles = self.news_agent.search_news(date, max_results=MAX_NEWS_ARTICLES)
            
            if company_articles:
                logger.info(f"✓ Collected {len(company_articles)} company articles:")
                for i, article in enumerate(company_articles, 1):
                    logger.info(f"  {i}. [{article['source']}] {article['title'][:60]}...")
            else:
                logger.warning("No company articles found")
            
            # Collect macro/market news
            macro_articles = self.news_agent.search_macro_news(date, max_results=MAX_NEWS_ARTICLES)
            
            if macro_articles:
                logger.info(f"✓ Collected {len(macro_articles)} macro articles:")
                for i, article in enumerate(macro_articles, 1):
                    logger.info(f"  {i}. [{article['source']}] {article['title'][:60]}...")
            else:
                logger.warning("No macro articles found")
            
            logger.info(f"✓ Total: {len(company_articles)} company + {len(macro_articles)} macro = {len(company_articles) + len(macro_articles)} articles")
            
            return company_articles, macro_articles
            
        except Exception as e:
            logger.error(f"Error collecting news: {str(e)}")
            return [], []
    
    def _analyze_sentiment(self, company_articles: List[Dict], macro_articles: List[Dict]) -> Dict:
        """
        Analyze sentiment of company and macro articles separately
        
        Args:
            company_articles: List of company-specific articles
            macro_articles: List of macro/market articles
        
        Returns:
            Sentiment analysis results with separate and combined scores
        """
        logger.info("\n🎯 STEP 3: Analyzing Sentiment")
        logger.info("-" * 60)
        
        try:
            # Use new method to analyze both types separately
            sentiment_result = self.sentiment_agent.analyze_articles_by_type(
                company_articles, macro_articles
            )
            
            logger.info(f"✓ Sentiment analysis complete:")
            logger.info(f"  Company Score: {sentiment_result['company_sentiment']:.2f}")
            logger.info(f"  Macro Score: {sentiment_result['macro_sentiment']:.2f}")
            logger.info(f"  Combined Score: {sentiment_result['combined_score']:.2f}")
            logger.info(f"  Confidence: {sentiment_result['combined_confidence']}")
            
            return sentiment_result
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {
                "company_sentiment": 0.0,
                "macro_sentiment": 0.0,
                "combined_score": 0.0,
                "combined_confidence": "Low",
                "company_factors": f"Error: {str(e)}",
                "macro_factors": f"Error: {str(e)}"
            }
    
    def _save_articles(self, company_articles: List[Dict], macro_articles: List[Dict], date: str) -> int:
        """
        Save company and macro articles to database
        
        Args:
            company_articles: List of company-specific articles
            macro_articles: List of macro/market articles
            date: Target date
        
        Returns:
            Number of articles saved
        """
        logger.info("\n💾 STEP 4: Saving Articles to Database")
        logger.info("-" * 60)
        
        saved_count = 0
        all_articles = company_articles + macro_articles
        
        for article in all_articles:
            article_data = {
                'date': date,
                'url': article['url'],
                'source': article['source'],
                'title': article['title'],
                'summary': article.get('snippet', ''),
                'sentiment_score': None,  # Individual scores not used yet
                'article_type': article.get('article_type', 'company')  # Store article type
            }
            
            if self.db.save_article(article_data):
                saved_count += 1
        
        logger.info(f"✓ Saved {saved_count}/{len(all_articles)} articles to database")
        logger.info(f"  ({len(company_articles)} company + {len(macro_articles)} macro)")
        return saved_count
    
    def _update_sentiment(self, date: str, sentiment_result: Dict, is_trading_day: bool) -> bool:
        """
        Update sentiment scores in database (company, macro, and combined)
        
        Args:
            date: Target date
            sentiment_result: Sentiment analysis results
            is_trading_day: Whether this is a trading day
        
        Returns:
            Success status
        """
        logger.info("\n📊 STEP 5: Updating Sentiment Scores")
        logger.info("-" * 60)
        
        company_sentiment = sentiment_result.get('company_sentiment', 0.0)
        macro_sentiment = sentiment_result.get('macro_sentiment', 0.0)
        combined_sentiment = sentiment_result.get('combined_score', 0.0)
        
        if is_trading_day:
            # Update today's sentiment with all three scores
            success = self.db.update_sentiment_scores(
                date, 
                company_sentiment, 
                macro_sentiment, 
                combined_sentiment
            )
            if success:
                logger.info(f"✓ Updated sentiment for {date}:")
                logger.info(f"  Company: {company_sentiment:.2f}")
                logger.info(f"  Macro: {macro_sentiment:.2f}")
                logger.info(f"  Combined: {combined_sentiment:.2f}")
            else:
                logger.error(f"Failed to update sentiment for {date}")
            return success
        else:
            # Weekend/Holiday: Update last trading day's sentiment
            last_trading_day = self.workflow.get_last_trading_day_for_update()
            if not last_trading_day:
                logger.warning("⚠️  No last trading day found in database")
                logger.warning("   Articles saved - sentiment will be calculated on next trading day")
                return True  # Not an error - articles are saved
            
            # Check if that day exists in database
            existing_data = self.db.get_daily_data(last_trading_day)
            if not existing_data:
                logger.warning(f"⚠️  Last trading day ({last_trading_day}) not in database yet")
                logger.warning("   Articles saved - sentiment will be calculated on next trading day")
                return True  # Not an error - articles are saved
            
            success = self.db.update_sentiment_scores(
                last_trading_day, 
                company_sentiment, 
                macro_sentiment, 
                combined_sentiment
            )
            if success:
                logger.info(f"✓ Updated last trading day ({last_trading_day}) sentiment: {combined_sentiment:.2f}")
                logger.info(f"  (Company: {company_sentiment:.2f}, Macro: {macro_sentiment:.2f})")
            else:
                logger.error(f"Failed to update sentiment for {last_trading_day}")
            return success
    
    def _update_sentiment_simple(self, trading_day: str, sentiment_result: Dict) -> bool:
        """
        Simple sentiment update - always updates the specified trading day
        
        Args:
            trading_day: The trading day to update (last available from Yahoo)
            sentiment_result: Sentiment analysis results
        
        Returns:
            Success status
        """
        logger.info("\n📊 STEP 5: Updating Sentiment Scores")
        logger.info("-" * 60)
        
        company_sentiment = sentiment_result.get('company_sentiment', 0.0)
        macro_sentiment = sentiment_result.get('macro_sentiment', 0.0)
        combined_sentiment = sentiment_result.get('combined_score', 0.0)
        
        success = self.db.update_sentiment_scores(
            trading_day, 
            company_sentiment, 
            macro_sentiment, 
            combined_sentiment
        )
        
        if success:
            logger.info(f"✓ Updated sentiment for {trading_day}:")
            logger.info(f"  Company: {company_sentiment:.2f}")
            logger.info(f"  Macro: {macro_sentiment:.2f}")
            logger.info(f"  Combined: {combined_sentiment:.2f}")
        else:
            logger.error(f"Failed to update sentiment for {trading_day}")
        
        return success
    
    def _make_prediction(self) -> Dict:
        """
        Make prediction for next trading day using ML model
        
        Returns:
            Prediction result dictionary
        """
        logger.info("\n🎯 STEP 6: Making Prediction")
        logger.info("-" * 60)
        
        # Check model status
        status = self.prediction_agent.get_model_status()
        
        if not status['can_train']:
            # Not enough data
            data_count = status['database_records']
            min_required = status['min_required']
            days_needed = min_required - data_count
            
            logger.warning(f"⚠️  Cannot predict - not enough data")
            logger.warning(f"   Have: {data_count} days")
            logger.warning(f"   Need: {min_required} days minimum")
            logger.warning(f"   Collect data for {days_needed} more days")
            
            return {
                'can_predict': False,
                'prediction': None,
                'confidence': 0.0,
                'message': f"Not enough data ({data_count}/{min_required} days)"
            }
        
        # Train model if needed
        if not status['is_trained']:
            logger.info("Training prediction model...")
            train_result = self.prediction_agent.train_model()
            if not train_result['success']:
                return {
                    'can_predict': False,
                    'prediction': None,
                    'confidence': 0.0,
                    'message': f"Training failed: {train_result['message']}"
                }
        
        # Make prediction
        prediction = self.prediction_agent.predict_next_day()
        
        if prediction['success']:
            logger.info(f"✓ Prediction: {prediction['prediction']}")
            logger.info(f"  Confidence: {prediction['confidence']:.1%}")
            logger.info(f"  Up probability: {prediction['probability_up']:.1%}")
            logger.info(f"  Down probability: {prediction['probability_down']:.1%}")
        else:
            logger.warning(f"Prediction failed: {prediction['message']}")
        
        return {
            'can_predict': prediction['success'],
            'prediction': prediction['prediction'],
            'confidence': prediction.get('confidence', 0.0),
            'probability_up': prediction.get('probability_up', 0.0),
            'probability_down': prediction.get('probability_down', 0.0),
            'message': prediction['message']
        }
    
    def _bootstrap_if_needed(self, current_date: str) -> None:
        """
        Bootstrap database if empty and market is closed
        Gets the last available trading day data from Yahoo Finance
        
        Args:
            current_date: Current date to check
        """
        try:
            # Check if database is empty
            data_count = self.db.get_data_count()
            if data_count > 0:
                return  # Database has data, no bootstrap needed
            
            # Check if market is closed today
            is_market_open = self.workflow.should_collect_market_data(current_date)
            if is_market_open:
                return  # Market is open, normal flow will work
            
            # Database is empty AND market is closed - bootstrap needed
            logger.info("\n🔧 BOOTSTRAP MODE")
            logger.info("-" * 60)
            logger.info("Database is empty and market is closed")
            logger.info("Fetching last available trading day from Yahoo Finance...")
            
            # Get last trading day from Yahoo Finance
            last_trading_day = self.market_fetcher.get_last_trading_day()
            if not last_trading_day:
                logger.error("Failed to get last trading day from Yahoo Finance")
                return
            
            logger.info(f"Last trading day: {last_trading_day}")
            
            # Fetch and save that day's market data
            market_data = self.market_fetcher.fetch_daily_data(last_trading_day)
            if not market_data:
                logger.error(f"Failed to fetch market data for {last_trading_day}")
                return
            
            # Save to database
            success = self.db.save_daily_data(market_data)
            if success:
                logger.info(f"✓ Bootstrapped database with {last_trading_day} market data")
                logger.info(f"  Close: ${market_data['close_price']:.2f}")
                logger.info(f"  Volume: {market_data['volume']:,}")
            else:
                logger.error("Failed to save bootstrap data to database")
            
            logger.info("-" * 60)
            
        except Exception as e:
            logger.error(f"Bootstrap failed: {str(e)}")
    
    def _process_orphaned_articles(self, current_date: str) -> None:
        """
        Process articles collected on weekends before any trading day data existed
        This handles the edge case of starting the project on a weekend
        
        Args:
            current_date: Current trading day
        """
        try:
            # Check if this is the first trading day (row 1 in database)
            data_count = self.db.get_data_count()
            if data_count != 1:
                return  # Not the first day, skip
            
            logger.info("\n🔄 Checking for orphaned weekend articles...")
            logger.info("-" * 60)
            
            # Get the last trading day date from the ONE row we have
            last_trading_day = self.db.get_last_trading_day_date()
            if not last_trading_day:
                return
            
            # Look for articles from before this date (weekend articles)
            orphaned_articles = self.db.get_articles_before_date(last_trading_day)
            
            if orphaned_articles:
                logger.info(f"✓ Found {len(orphaned_articles)} orphaned articles from before {last_trading_day}")
                
                # Re-analyze sentiment including these articles
                all_articles = orphaned_articles + self.db.get_articles_for_date(current_date)
                
                if all_articles:
                    logger.info(f"Re-analyzing sentiment with {len(all_articles)} total articles...")
                    sentiment_result = self.sentiment_agent.analyze_articles_by_type(all_articles)
                    
                    if sentiment_result:
                        self.db.update_sentiment_scores(
                            current_date, 
                            sentiment_result['company_sentiment'],
                            sentiment_result['macro_sentiment'],
                            sentiment_result['combined_score']
                        )
                        logger.info(f"✓ Updated sentiment including orphaned articles: {sentiment_result['combined_score']:.2f}")
            else:
                logger.info("✓ No orphaned articles found")
                
        except Exception as e:
            logger.warning(f"Error processing orphaned articles: {str(e)}")
    
    def get_workflow_summary(self) -> Dict:
        """
        Get summary of system status
        
        Returns:
            Dictionary with system summary
        """
        return {
            "total_trading_days": self.db.get_data_count(),
            "last_trading_day": self.db.get_last_trading_day_date(),
            "market_open_today": self.market_fetcher.is_market_open(),
            "latest_price": self.market_fetcher.get_latest_price(),
            "components_status": {
                "news_agent": "Ready",
                "sentiment_agent": "Ready",
                "market_fetcher": "Ready",
                "database": "Connected"
            }
        }


# ============================================
# MODULE TEST
# ============================================
if __name__ == "__main__":
    """Test the orchestrator agent"""
    from config.settings import OPENAI_API_KEY, SERPER_API_KEY
    
    logger = setup_logger("test_orchestrator")
    log_section_header(logger, "Orchestrator Agent Test")
    
    # Check API keys
    if not OPENAI_API_KEY or not SERPER_API_KEY:
        logger.error("API keys not set. This test requires:")
        logger.error("  - OPENAI_API_KEY (for sentiment analysis)")
        logger.error("  - SERPER_API_KEY (for news search)")
        logger.info("\nShowing dry-run test without API calls...")
        
        print("\n" + "="*60)
        print("Orchestrator Workflow (without API keys):")
        print("="*60)
        print("""
The orchestrator coordinates:

1. Workflow Manager
   → Determines if market is open
   → Decides which workflow to run

2. Market Data Fetcher (if trading day)
   → Fetches NVIDIA stock data
   → Saves to daily_data table

3. News Agent
   → Searches for NVIDIA news
   → Filters by trusted sources
   → Returns top 3 articles

4. Sentiment Agent
   → Analyzes articles with GPT-4
   → Generates sentiment score
   → Provides confidence level

5. Database Manager
   → Saves articles to articles table
   → Updates sentiment score
   → Handles weekend accumulation

TRADING DAY:
  - Collect market data + articles
  - Update current day's sentiment

WEEKEND/HOLIDAY:
  - Collect articles only
  - Update LAST TRADING DAY's sentiment
        """)
        print("="*60)
    else:
        # Run actual test
        orchestrator = OrchestratorAgent()
        
        logger.info("\nRunning workflow summary...")
        summary = orchestrator.get_workflow_summary()
        
        print("\n" + "="*60)
        print("SYSTEM SUMMARY")
        print("="*60)
        for key, value in summary.items():
            if isinstance(value, dict):
                print(f"\n{key}:")
                for k, v in value.items():
                    print(f"  {k}: {v}")
            else:
                print(f"{key}: {value}")
        print("="*60)
        
        # Test workflow (dry run)
        logger.info("\n\nRunning test workflow (dry run - no database saves)...")
        result = orchestrator.run_daily_workflow(dry_run=True)
        
        print("\n" + "="*60)
        print("WORKFLOW RESULT")
        print("="*60)
        print(f"Date: {result['date']}")
        print(f"Success: {result['success']}")
        print(f"Trading Day: {result['is_trading_day']}")
        print(f"Market Data: {result['market_data_collected']}")
        print(f"Articles: {result['articles_collected']}")
        print(f"Sentiment: {result['sentiment_score']:.2f}")
        print(f"Confidence: {result['sentiment_confidence']}")
        if result.get('errors'):
            print(f"Errors: {result['errors']}")
        print("="*60)
        
        logger.info("\n✓ Orchestrator test complete!")
