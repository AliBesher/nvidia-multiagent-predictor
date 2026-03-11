"""
Orchestrator Agent
Coordinates all agents and manages the daily workflow
"""

from datetime import datetime
from typing import Dict, Optional, List
import pytz
from agents.base_agent import BaseAgent
from agents.news_agent import NewsAgent
from agents.sentiment_agent import SentimentAgent
from agents.prediction_agent import PredictionAgent
from agents.strategy_agent import StrategyAgent
from data.market_data_fetcher import MarketDataFetcher
from data.database_manager import DatabaseManager
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
        self.strategy_agent = StrategyAgent()
        self.market_fetcher = MarketDataFetcher()
        self.db = DatabaseManager()
        self.workflow = WorkflowManager()
        
        # Initialize timezone objects for automatic DST handling
        self.est_tz = pytz.timezone('America/New_York')
        self.ist_tz = pytz.timezone('Asia/Jerusalem')
        
        logger.info("OrchestratorAgent initialized with all components and timezone logic")
    
    
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
            
            # Step 2: Collect news articles (company + macro) for today with timezone categorization
            company_articles, macro_articles = self._collect_news_articles(ny_today)
            
            # Step 2.5: Apply Israel timezone categorization logic
            categorized_articles = self._apply_israel_timezone_logic(company_articles, macro_articles)
            result["articles_collected"] = len(company_articles) + len(macro_articles)
            result["company_article_count"] = len(company_articles)
            result["macro_article_count"] = len(macro_articles)
            result["intraday_articles"] = categorized_articles["intraday_count"]
            result["gap_force_articles"] = categorized_articles["gap_force_count"]
            result["timezone_summary"] = categorized_articles["summary"]
            
            if not company_articles and not macro_articles:
                logger.warning("No new articles collected - sentiment analysis skipped")
                result["errors"].append("No articles found")
            else:
                # Step 3: Analyze sentiment (separate company and macro) with timezone context
                sentiment_result = self._analyze_sentiment_with_timezone(company_articles, macro_articles, categorized_articles)
                result["company_sentiment"] = sentiment_result["company_sentiment"]
                result["macro_sentiment"] = sentiment_result["macro_sentiment"]
                result["sentiment_score"] = sentiment_result["combined_score"]
                result["sentiment_confidence"] = sentiment_result["combined_confidence"]
                result["company_factors"] = sentiment_result.get("company_factors", "")
                result["macro_factors"] = sentiment_result.get("macro_factors", "")
                result["timezone_impact"] = sentiment_result.get("timezone_impact", "")
                
                # Step 4: Save articles to database (linked to last trading day)
                if not dry_run:
                    self._save_articles(company_articles, macro_articles, last_trading_day)
                
                # Step 5: Update sentiment for last trading day
                if not dry_run:
                    self._update_sentiment_simple(last_trading_day, sentiment_result)
            
            # Step 6: Calculate Hybrid Signal with Dynamic Strategy Weights
            hybrid_result = self._calculate_hybrid_prediction(sentiment_result, last_trading_day, dry_run)
            result["hybrid_prediction"] = hybrid_result.get("recommendation")  # Use recommendation as signal type
            result["hybrid_confidence"] = hybrid_result.get("hybrid_confidence") 
            result["hybrid_final_gravity"] = hybrid_result.get("final_gravity")
            result["strategy_weights"] = hybrid_result.get("strategy_weights")
            result["technical_score"] = hybrid_result.get("technical_score", 0.0)
            result["info_gravity"] = hybrid_result.get("info_gravity", 0.0)
            
            # Step 7: Make ML prediction (if enough data) as additional validation
            prediction_result = self._make_prediction()
            result["prediction"] = prediction_result.get("prediction")
            result["prediction_confidence"] = prediction_result.get("confidence", 0.0)
            result["can_predict"] = prediction_result.get("can_predict", False)
            result["prediction_message"] = prediction_result.get("message", "")
            
            # Step 8: Make ML Opening prediction (GAP UP/DOWN)
            opening_result = self._make_opening_prediction()
            result["opening_prediction"] = opening_result.get("prediction")
            result["opening_confidence"] = opening_result.get("confidence", 0.0)
            result["can_predict_opening"] = opening_result.get("can_predict", False)
            result["opening_message"] = opening_result.get("message", "")
            
            result["success"] = True
            logger.info(f"\n{'='*60}")
            logger.info(f"✓ Workflow completed successfully")
            logger.info(f"  Market data: {last_trading_day}")
            logger.info(f"  News collected: {ny_today}")
            
            # ── FINAL 3-RESULT SUMMARY ──
            logger.info(f"\n{'─'*60}")
            logger.info(f"📋 PREDICTION SUMMARY (3 Models)")
            logger.info(f"{'─'*60}")
            
            hg = result.get('hybrid_final_gravity', 0.0)
            logger.info(f"  🔬 Hybrid Gravity:   {hg:+.2f} → {result.get('hybrid_prediction', 'N/A')}")
            
            if result.get('can_predict'):
                logger.info(f"  🎯 ML Close:         {result['prediction']} ({result['prediction_confidence']:.1%})")
            else:
                logger.info(f"  🎯 ML Close:         Not ready")
            
            if result.get('can_predict_opening'):
                logger.info(f"  🌅 ML Opening:       {result['opening_prediction']} ({result['opening_confidence']:.1%})")
            else:
                logger.info(f"  🌅 ML Opening:       Not ready")
            
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
    
    def _apply_israel_timezone_logic(self, company_articles: List[Dict], macro_articles: List[Dict]) -> Dict:
        """
        Apply Israel timezone logic to categorize news articles
        
        Rules:
        - If script runs at 00:00 IST:
          * News from 16:30 to 23:00 IST = 'Intraday News' (reflected in current price)
          * News from 23:00 to 00:00 IST = 'Gap Force News' (impacts tomorrow's opening)
        - Dynamic EST ↔ IST conversion handles Daylight Saving Time automatically
        
        Args:
            company_articles: List of company-specific articles
            macro_articles: List of macro/market articles
        
        Returns:
            Dictionary with categorization results
        """
        logger.info("\n*** STEP 2.5: Applying Israel Timezone Logic")
        logger.info("-" * 60)
        
        try:
            # Get current time in both timezones
            ny_now = datetime.now(self.est_tz)
            israel_now = ny_now.astimezone(self.ist_tz)
            
            logger.info(f"Current EST: {ny_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            logger.info(f"Current IST: {israel_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            # Calculate timezone offset (dynamic for DST)
            offset_hours = (israel_now.utcoffset() - ny_now.utcoffset()).total_seconds() / 3600
            logger.info(f"Dynamic IST-EST offset: +{offset_hours:.1f} hours")
            
            all_articles = company_articles + macro_articles
            intraday_articles = []
            gap_force_articles = []
            
            for article in all_articles:
                # Parse article timestamp and convert to Israel timezone
                article_israel_time = self._convert_article_to_israel_time(article)
                
                if article_israel_time:
                    article_hour = article_israel_time.hour
                    article_minute = article_israel_time.minute
                    
                    # Categorize based on Israel time
                    if (article_hour == 16 and article_minute >= 30) or (17 <= article_hour < 23):
                        # 16:30-23:00 IST = Intraday News
                        article['timezone_category'] = 'intraday'
                        article['israel_timestamp'] = article_israel_time.strftime('%H:%M IST')
                        intraday_articles.append(article)
                    elif article_hour == 23 or (article_hour == 0):
                        # 23:00-00:00 IST = Gap Force News  
                        article['timezone_category'] = 'gap_force'
                        article['israel_timestamp'] = article_israel_time.strftime('%H:%M IST')
                        gap_force_articles.append(article)
                    else:
                        # Other times - general categorization
                        article['timezone_category'] = 'other'
                        article['israel_timestamp'] = article_israel_time.strftime('%H:%M IST')
                else:
                    # Unable to determine timestamp
                    article['timezone_category'] = 'unknown'
                    article['israel_timestamp'] = 'Unknown time'
            
            # Log categorization results
            logger.info(f"*** Timezone categorization complete:")
            logger.info(f"  Intraday News (16:30-23:00 IST): {len(intraday_articles)} articles")
            logger.info(f"  Gap Force News (23:00-00:00 IST): {len(gap_force_articles)} articles")
            logger.info(f"  Other/Unknown: {len(all_articles) - len(intraday_articles) - len(gap_force_articles)} articles")
            
            if intraday_articles:
                logger.info("  Intraday articles:")
                for article in intraday_articles[:3]:  # Show first 3
                    logger.info(f"    [{article['israel_timestamp']}] {article['title'][:50]}...")
            
            if gap_force_articles:
                logger.info("  Gap Force articles:")
                for article in gap_force_articles[:3]:  # Show first 3
                    logger.info(f"    [{article['israel_timestamp']}] {article['title'][:50]}...")
            
            return {
                "intraday_articles": intraday_articles,
                "gap_force_articles": gap_force_articles,
                "intraday_count": len(intraday_articles),
                "gap_force_count": len(gap_force_articles),
                "offset_hours": offset_hours,
                "summary": f"Intraday: {len(intraday_articles)}, Gap Force: {len(gap_force_articles)}"
            }
            
        except Exception as e:
            logger.error(f"Error applying timezone logic: {str(e)}")
            return {
                "intraday_articles": [],
                "gap_force_articles": [],
                "intraday_count": 0,
                "gap_force_count": 0,
                "offset_hours": 7.0,  # Default offset
                "summary": f"Error: {str(e)}"
            }
    
    def _convert_article_to_israel_time(self, article: Dict) -> Optional[datetime]:
        """
        Convert article timestamp to Israel timezone
        
        Args:
            article: Article dictionary with timestamp information
        
        Returns:
            datetime object in Israel timezone or None if conversion fails
        """
        try:
            # Try to parse the article timestamp
            if 'published_date' in article and article['published_date']:
                timestamp_str = article['published_date']
            elif 'date' in article and article['date']:
                timestamp_str = article['date']
            else:
                # Use current time as fallback
                return datetime.now(self.ist_tz)
            
            # Parse the timestamp (handle various formats)
            from dateutil import parser
            article_dt = parser.parse(timestamp_str)
            
            # If timezone-naive, assume EST
            if article_dt.tzinfo is None:
                article_dt = self.est_tz.localize(article_dt)
            
            # Convert to Israel timezone
            israel_dt = article_dt.astimezone(self.ist_tz)
            return israel_dt
            
        except Exception as e:
            # If parsing fails, use current Israel time
            logger.warning(f"Could not parse article timestamp: {str(e)}")
            return datetime.now(self.ist_tz)
    
    def _analyze_sentiment_with_timezone(self, company_articles: List[Dict], macro_articles: List[Dict], timezone_data: Dict) -> Dict:
        """
        Analyze sentiment of company and macro articles with timezone context
        
        Args:
            company_articles: List of company-specific articles
            macro_articles: List of macro/market articles
            timezone_data: Timezone categorization data
        
        Returns:
            Sentiment analysis results with timezone impact information
        """
        logger.info("\n🎯 STEP 3: Analyzing Sentiment with Timezone Context")
        logger.info("-" * 60)
        
        try:
            # Use existing sentiment analysis method
            sentiment_result = self.sentiment_agent.analyze_articles_by_type(
                company_articles, macro_articles
            )
            
            # Add timezone impact analysis
            intraday_count = timezone_data["intraday_count"]
            gap_force_count = timezone_data["gap_force_count"]
            
            timezone_impact = ""
            if gap_force_count > 0:
                timezone_impact = f"Gap Force Risk: {gap_force_count} post-market articles may impact tomorrow's opening. "
            if intraday_count > 0:
                timezone_impact += f"Intraday Context: {intraday_count} articles reflect current market conditions."
            
            sentiment_result["timezone_impact"] = timezone_impact
            
            logger.info(f"✓ Sentiment analysis with timezone context complete:")
            logger.info(f"  Company Score: {sentiment_result['company_sentiment']:.2f}")
            logger.info(f"  Macro Score: {sentiment_result['macro_sentiment']:.2f}")
            logger.info(f"  Combined Score: {sentiment_result['combined_score']:.2f}")
            logger.info(f"  Confidence: {sentiment_result['combined_confidence']}")
            logger.info(f"  Timezone Impact: {timezone_impact}")
            
            return sentiment_result
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment with timezone: {str(e)}")
            return {
                "company_sentiment": 0.0,
                "macro_sentiment": 0.0,
                "combined_score": 0.0,
                "combined_confidence": "Low",
                "company_factors": f"Error: {str(e)}",
                "macro_factors": f"Error: {str(e)}",
                "timezone_impact": f"Timezone analysis failed: {str(e)}"
            }
    
    def _save_articles(self, company_articles: List[Dict], macro_articles: List[Dict], date: str) -> int:
        """
        Save company and macro articles to database with individual sentiment scores
        
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
            # Get sentiment score from article if available (set by sentiment analysis)
            sentiment_score = article.get('sentiment_score', None)
            
            article_data = {
                'date': date,
                'url': article['url'],
                'source': article['source'],
                'title': article['title'],
                'summary': article.get('snippet', ''),  # Keep short snippet
                'full_content': article.get('full_content', ''),  # Full scraped content
                'sentiment_score': sentiment_score,  # Now uses actual individual scores
                'article_type': article.get('article_type', 'company')  # Store article type
            }
            
            if self.db.save_article(article_data):
                saved_count += 1
                if sentiment_score is not None:
                    logger.info(f"✓ Saved article with sentiment score {sentiment_score:.2f}: {article['title'][:50]}...")
        
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
            # Update today's sentiment with all three scores plus gravity data
            success = self.db.update_sentiment_scores(
                date, 
                company_sentiment, 
                macro_sentiment, 
                combined_sentiment,
                sentiment_result.get('combined_range', ''),
                sentiment_result.get('combined_entropy', 'Low')
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
                combined_sentiment,
                sentiment_result.get('combined_range', ''),
                sentiment_result.get('combined_entropy', 'Low')
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
            combined_sentiment,
            sentiment_result.get('combined_range', ''),
            sentiment_result.get('combined_entropy', 'Low')
        )
        
        if success:
            logger.info(f"✓ Updated sentiment for {trading_day}:")
            logger.info(f"  Company: {company_sentiment:.2f}")
            logger.info(f"  Macro: {macro_sentiment:.2f}")
            logger.info(f"  Combined: {combined_sentiment:.2f}")
        else:
            logger.error(f"Failed to update sentiment for {trading_day}")
        
        return success
    
    def _calculate_hybrid_prediction(self, sentiment_result: Dict, date: str, dry_run: bool = False) -> Dict:
        """
        Calculate hybrid prediction using StrategyAgent for dynamic weights
        
        Args:
            sentiment_result: Results from sentiment analysis
            date: Date for prediction
            dry_run: If True, don't save to database
            
        Returns:
            Hybrid prediction result dictionary
        """
        logger.info("\n🔬 STEP 6: Calculating Hybrid Prediction with Dynamic Strategy")
        logger.info("-" * 60)
        
        try:
            info_gravity = sentiment_result.get('combined_score', 0.0)
            
            # Prepare news summary for strategy agent
            article_count = sentiment_result.get('article_count', {})
            news_summary = {
                'final_sentiment': info_gravity,
                'company_count': article_count.get('company', 0),
                'macro_count': article_count.get('macro', 0),
                'company_sentiment': sentiment_result.get('company_sentiment', 0.0),
                'macro_sentiment': sentiment_result.get('macro_sentiment', 0.0)
            }
            
            # Calculate hybrid signal with dynamic weights
            hybrid_result = self.calculate_hybrid_signal(date, info_gravity, news_summary)
            
            # Save hybrid prediction to database (if not dry_run)
            if not dry_run:
                final_gravity = hybrid_result.get('final_gravity', 0.0)
                confidence = hybrid_result.get('hybrid_confidence', 'Low')
                success = self.db.save_hybrid_prediction(date, final_gravity, confidence)
                if success:
                    logger.info(f"✓ Hybrid prediction saved to database")
                else:
                    logger.warning(f"Failed to save hybrid prediction to database")
            
            logger.info(f"✓ Hybrid prediction complete:")
            logger.info(f"  Signal: {hybrid_result.get('recommendation', 'N/A')}")
            logger.info(f"  Direction: {hybrid_result.get('signal_alignment', 'N/A')}")
            logger.info(f"  Final Gravity: {hybrid_result.get('final_gravity', 0.0):+.2f}")
            logger.info(f"  Confidence: {hybrid_result.get('hybrid_confidence', 'N/A')}")
            
            weights = hybrid_result.get('strategy_weights', {})
            logger.info(f"  Dynamic Weights: S{weights.get('sentiment', 0.6):.0%}/T{weights.get('technical', 0.4):.0%}")
            
            return hybrid_result
            
        except Exception as e:
            logger.error(f"Error calculating hybrid prediction: {str(e)}")
            return {
                "signal_type": "ERROR",
                "signal_direction": "UNKNOWN", 
                "final_gravity": 0.0,
                "confidence": "Low",
                "strategy_weights": {"sentiment": 0.6, "technical": 0.4}
            }

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
    
    def _make_opening_prediction(self) -> Dict:
        """
        Make opening prediction for next trading day using ML model
        Predicts GAP UP or GAP DOWN (next_day_open vs close_price)
        
        Returns:
            Opening prediction result dictionary
        """
        logger.info("\n🌅 STEP 8: Making Opening Prediction")
        logger.info("-" * 60)
        
        # Check model status
        status = self.prediction_agent.get_model_status()
        opening_status = status.get('opening_model', {})
        
        if not status.get('can_train', False):
            data_count = status['database_records']
            min_required = status['min_required']
            days_needed = min_required - data_count
            
            logger.warning(f"⚠️  Cannot predict opening - not enough data")
            logger.warning(f"   Have: {data_count} days")
            logger.warning(f"   Need: {min_required} days minimum")
            
            return {
                'can_predict': False,
                'prediction': None,
                'confidence': 0.0,
                'message': f"Not enough data ({data_count}/{min_required} days)"
            }
        
        # Train opening model if needed
        if not opening_status.get('is_trained', False):
            logger.info("Training opening prediction model...")
            train_result = self.prediction_agent.train_opening_model()
            if not train_result['success']:
                return {
                    'can_predict': False,
                    'prediction': None,
                    'confidence': 0.0,
                    'message': f"Opening training failed: {train_result['message']}"
                }
        
        # Make opening prediction
        prediction = self.prediction_agent.predict_next_day_opening()
        
        if prediction['success']:
            logger.info(f"✓ Opening Prediction: {prediction['prediction']}")
            logger.info(f"  Confidence: {prediction['confidence']:.1%}")
            logger.info(f"  Gap Up probability: {prediction.get('probability_up', 0):.1%}")
            logger.info(f"  Gap Down probability: {prediction.get('probability_down', 0):.1%}")
        else:
            logger.warning(f"Opening prediction failed: {prediction['message']}")
        
        return {
            'can_predict': prediction['success'],
            'prediction': prediction.get('prediction'),
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
                    # Separate into company and macro articles
                    company_articles = [a for a in all_articles if any(keyword in a['title'].lower() for keyword in ['nvidia', 'nvda'])]
                    macro_articles = [a for a in all_articles if a not in company_articles]
                    sentiment_result = self.sentiment_agent.analyze_articles_by_type(company_articles, macro_articles)
                    
                    if sentiment_result:
                        self.db.update_sentiment_scores(
                            current_date, 
                            sentiment_result['company_sentiment'],
                            sentiment_result['macro_sentiment'],
                            sentiment_result['combined_score'],
                            sentiment_result.get('combined_range', ''),
                            sentiment_result.get('combined_entropy', 'Low')
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
    
    def calculate_hybrid_signal(self, date: str, info_gravity: float, news_summary: Optional[Dict] = None) -> Dict:
        """
        Calculate hybrid signal combining informational gravity with technical analysis using dynamic weights
        
        Formula: Final_Gravity = (Info_Gravity × Dynamic_Sentiment_Weight) + (Technical_Score × Dynamic_Technical_Weight)
        
        Args:
            date: Date to analyze
            info_gravity: Sentiment-based informational gravity score
            news_summary: Summary of news analysis for strategy determination
            
        Returns:
            Dictionary with hybrid analysis results
        """
        logger.info(f"\n🔬 CALCULATING HYBRID SIGNAL FOR {date} (DYNAMIC WEIGHTS)")
        logger.info("=" * 70)
        
        try:
            # Get technical analysis data
            technical_data = self.market_fetcher.fetch_technical_data(date)
            
            if not technical_data:
                logger.warning(f"No technical data available for {date}, using info gravity only")
                return {
                    "date": date,
                    "info_gravity": info_gravity,
                    "technical_score": 0.0,
                    "final_gravity": info_gravity,
                    "hybrid_confidence": "Low - No technical data",
                    "technical_breakdown": "No data available",
                    "strategy_weights": {
                        "sentiment": 1.0,
                        "technical": 0.0,
                        "regime_analysis": "No technical data - full sentiment weight",
                        "strategic_reasoning": "Fallback to sentiment-only analysis"
                    },
                    "recommendation": self._get_signal_recommendation(info_gravity)
                }
            
            # Extract technical score and indicators
            technical_score = technical_data['technical_score']
            rsi = technical_data.get('rsi', 50)
            momentum_3d = technical_data.get('momentum_3d', 0)
            
            # Prepare data for StrategyAgent
            news_data = news_summary or {
                'final_sentiment': info_gravity,
                'company_count': 3,  # Default fallback
                'macro_count': 3     # Default fallback
            }
            
            tech_data = {
                'rsi': rsi,
                'momentum_3d': momentum_3d,
                'tech_score': technical_score,
                # New indicators for enhanced strategy decisions
                'bollinger_pctb': technical_data.get('bollinger_pctb', 0.5),
                'bollinger_width': technical_data.get('bollinger_width', 0),
                'bollinger_position': technical_data.get('bollinger_position', 'MIDDLE'),
                'atr_percent': technical_data.get('atr_percent', 0),
                'volatility_level': technical_data.get('volatility_level', 'MODERATE'),
                'volume_ratio': technical_data.get('volume_ratio', 1.0),
                'volume_signal': technical_data.get('volume_signal', 'NORMAL'),
            }
            
            # Get dynamic weights from StrategyAgent
            strategy = self.strategy_agent.determine_daily_strategy(news_data, tech_data)
            
            # Extract dynamic weights
            sentiment_weight = strategy['applied_weights']['sentiment']
            technical_weight = strategy['applied_weights']['technical']
            
            # DYNAMIC HYBRID FORMULA: Apply strategy-determined weights
            final_gravity = (float(info_gravity) * sentiment_weight) + (float(technical_score) * technical_weight)
            
            # Determine confidence based on alignment
            signal_alignment = self._analyze_signal_alignment(info_gravity, technical_score)
            
            # Create technical breakdown
            technical_breakdown = self._format_technical_breakdown_dynamic(technical_data, strategy)
            
            # Get recommendation
            recommendation = self._get_hybrid_recommendation(info_gravity, technical_score, final_gravity, signal_alignment)
            
            # Log detailed analysis
            logger.info(f"🧠 STRATEGY ANALYSIS:")
            logger.info(f"  Regime: {strategy['regime_analysis']}")
            logger.info(f"  Weights: Sentiment {sentiment_weight:.1%} | Technical {technical_weight:.1%}")
            logger.info(f"📊 HYBRID CALCULATION:")
            logger.info(f"  Info Gravity (Sentiment): {info_gravity:+.2f} × {sentiment_weight:.1%} = {info_gravity * sentiment_weight:+.2f}")
            logger.info(f"  Technical Score:          {technical_score:+.2f} × {technical_weight:.1%} = {technical_score * technical_weight:+.2f}")
            logger.info(f"  Technical Confidence:     {technical_data.get('confidence_level', 0):.0f}%")
            logger.info(f"  Final Hybrid Gravity:     {final_gravity:+.2f}")
            logger.info(f"  Signal Alignment:         {signal_alignment['status']}")
            logger.info(f"  Confidence Level:         {signal_alignment['confidence']}")
            logger.info(f"  Recommendation:           {recommendation}")
            
            return {
                "date": date,
                "info_gravity": info_gravity,
                "technical_score": technical_score,
                "final_gravity": final_gravity,
                "hybrid_confidence": signal_alignment['confidence'],
                "signal_alignment": signal_alignment['status'],
                "technical_breakdown": technical_breakdown,
                "strategy_weights": {
                    "sentiment": sentiment_weight,
                    "technical": technical_weight,
                    "regime_analysis": strategy['regime_analysis'],
                    "strategic_reasoning": strategy['strategic_reasoning'],
                    "boundary_check": strategy['boundary_check']
                },
                "recommendation": recommendation,
                "rsi": technical_data.get('rsi'),
                "momentum_3d": technical_data.get('momentum_3d'),
                "ma_position": technical_data.get('ma_position'),
                "bollinger_position": technical_data.get('bollinger_position'),
                "bollinger_pctb": technical_data.get('bollinger_pctb'),
                "volume_ratio": technical_data.get('volume_ratio'),
                "volume_signal": technical_data.get('volume_signal'),
                "atr_percent": technical_data.get('atr_percent'),
                "volatility_level": technical_data.get('volatility_level'),
                # Physics-based scoring metadata
                "technical_confidence": technical_data.get('confidence_level'),
                "score_breakdown": technical_data.get('score_breakdown', {}),
            }
            
        except Exception as e:
            logger.error(f"Error calculating hybrid signal: {str(e)}")
            return {
                "date": date,
                "info_gravity": info_gravity,
                "technical_score": 0.0,
                "final_gravity": info_gravity,
                "hybrid_confidence": "Error",
                "technical_breakdown": f"Error: {str(e)}",
                "recommendation": "Unable to calculate hybrid signal"
            }
    
    def _analyze_signal_alignment(self, info_gravity: float, technical_score: float) -> Dict:
        """
        Analyze alignment between informational and technical signals
        
        Args:
            info_gravity: Sentiment-based score
            technical_score: Technical analysis score
            
        Returns:
            Dictionary with alignment analysis
        """
        # Convert to floats to ensure proper comparison
        info_gravity = float(info_gravity)
        technical_score = float(technical_score)
        
        info_direction = "UP" if info_gravity > 0 else "DOWN"
        tech_direction = "UP" if technical_score > 0 else "DOWN"
        
        if info_direction == tech_direction:
            # Signals align
            strength = min(abs(info_gravity), abs(technical_score))
            if strength > 5:
                return {"status": "Strong Alignment", "confidence": "High"}
            elif strength > 2:
                return {"status": "Moderate Alignment", "confidence": "Medium"}
            else:
                return {"status": "Weak Alignment", "confidence": "Low"}
        else:
            # Signals conflict
            info_strength = abs(info_gravity)
            tech_strength = abs(technical_score)
            
            if abs(info_strength - tech_strength) < 2:
                return {"status": "Signal Conflict - Equal Strength", "confidence": "Very Low"}
            elif info_strength > tech_strength:
                return {"status": "Info Dominance", "confidence": "Low-Medium"}
            else:
                return {"status": "Technical Dominance", "confidence": "Low-Medium"}
    
    def _format_technical_breakdown(self, technical_data: Dict) -> str:
        """
        Format technical data into readable breakdown (legacy version)
        
        Args:
            technical_data: Technical analysis data
            
        Returns:
            Formatted breakdown string
        """
        try:
            breakdown = f"RSI: {technical_data['rsi']} ({technical_data['rsi_pressure']}), "
            breakdown += f"Momentum: {technical_data['momentum_3d']:+.1f}% ({technical_data['momentum_direction']}), "
            breakdown += f"MA Position: {technical_data['ma_position']}"
            return breakdown
        except Exception as e:
            return f"Technical breakdown error: {str(e)}"
    
    def _format_technical_breakdown_dynamic(self, technical_data: Dict, strategy: Dict) -> str:
        """
        Format technical data with dynamic weight strategy analysis
        
        Args:
            technical_data: Technical analysis data
            strategy: Strategy analysis from StrategyAgent
            
        Returns:
            Formatted breakdown string with strategy context
        """
        try:
            weights = strategy['applied_weights']
            breakdown = f"📊 DYNAMIC HYBRID ANALYSIS:\n"
            breakdown += f"  Sentiment Weight: {weights['sentiment']:.1%} | Technical Weight: {weights['technical']:.1%}\n"
            breakdown += f"  Info Gravity: {technical_data.get('info_gravity', 0):+.2f} × {weights['sentiment']:.1%} = {technical_data.get('info_gravity', 0) * weights['sentiment']:+.2f}\n"
            breakdown += f"  Technical Score: {technical_data['technical_score']:+.2f} × {weights['technical']:.1%} = {technical_data['technical_score'] * weights['technical']:+.2f}\n"
            # Physics-based confidence
            conf = technical_data.get('confidence_level', 0)
            breakdown += f"  Technical Confidence: {conf:.0f}%\n"
            breakdown += f"\n🧠 STRATEGY REGIME: {strategy['regime_analysis']}\n"
            breakdown += f"📈 TECHNICAL DETAILS: RSI {technical_data['rsi']} ({technical_data['rsi_pressure']}), "
            breakdown += f"Momentum {technical_data['momentum_3d']:+.1f}% ({technical_data['momentum_direction']})\n"
            # New indicators
            bb_pos = technical_data.get('bollinger_position', 'N/A')
            bb_pctb = technical_data.get('bollinger_pctb', 0)
            vol_sig = technical_data.get('volume_signal', 'N/A')
            vol_ratio = technical_data.get('volume_ratio', 1.0)
            atr_pct = technical_data.get('atr_percent', 0)
            vol_level = technical_data.get('volatility_level', 'N/A')
            breakdown += f"  Bollinger: {bb_pos} (%B={bb_pctb:.2f}), Volume: {vol_ratio:.1f}x ({vol_sig}), ATR: {atr_pct:.1f}% ({vol_level})\n"
            # Physics Score Breakdown
            sb = technical_data.get('score_breakdown', {})
            if sb:
                breakdown += f"⚛️ PHYSICS BREAKDOWN: Mom_F={sb.get('momentum_force', 0):+.2f}, RSI_P={sb.get('rsi_penalty', 0):+.2f}, "
                breakdown += f"BB_S={sb.get('bollinger_signal', 0):+.2f}, MA_C={sb.get('ma_convergence', 0):+.2f} → Raw={sb.get('total_raw', 0):+.2f}"
            return breakdown
        except Exception as e:
            return f"Dynamic breakdown error: {str(e)}"
    
    def _get_signal_recommendation(self, score: float) -> str:
        """
        Get recommendation based on single score
        
        Args:
            score: Signal score
            
        Returns:
            Recommendation string
        """
        if score > 5:
            return "Strong BUY signal"
        elif score > 2:
            return "Moderate BUY signal"
        elif score > 0:
            return "Weak BUY signal"
        elif score < -5:
            return "Strong SELL signal"
        elif score < -2:
            return "Moderate SELL signal"
        else:
            return "Weak SELL signal"
    
    def _get_hybrid_recommendation(self, info_gravity: float, technical_score: float, 
                                 final_gravity: float, alignment: Dict) -> str:
        """
        Get recommendation based on hybrid analysis
        
        Args:
            info_gravity: Information gravity score
            technical_score: Technical score
            final_gravity: Combined final score
            alignment: Signal alignment data
            
        Returns:
            Hybrid recommendation string
        """
        base_rec = self._get_signal_recommendation(final_gravity)
        
        # Add context based on alignment
        if alignment['status'] == "Signal Conflict - Equal Strength":
            return f"{base_rec} (⚠️ CONFLICTING SIGNALS - Use caution)"
        elif "Conflict" in alignment['status']:
            return f"{base_rec} (Mixed signals - {alignment['status']})"
        elif alignment['confidence'] == "High":
            return f"{base_rec} (✅ Strong agreement between sentiment & technicals)"
        else:
            return f"{base_rec} ({alignment['status']})"


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
