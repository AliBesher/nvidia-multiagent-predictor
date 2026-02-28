"""
Sentiment Agent with Temporal Physics
Analyzes news articles and generates sentiment scores using GPT-4 with time-based decay
"""

from typing import List, Dict, Optional
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime, timezone
import pytz
import json
from agents.base_agent import BaseAgent
from config.settings import SENTIMENT_SCALE
from config.trusted_sources import get_source_tier
from utils.logger import setup_logger
import re

logger = setup_logger(__name__)

class SentimentAgent(BaseAgent):
    """
    Agent for analyzing sentiment from news articles using GPT-4 with Temporal Physics.
    Operates strictly on New York Time (EST/EDT) for financial accuracy.
    Implements time-based decay for news aging, dynamic weighting, and post-market awareness.
    """
    
    def __init__(self):
        super().__init__("SentimentAgent")
        
        # PRIMARY TIMEZONE REFERENCE: New York (EST/EDT)
        self.ny_tz = pytz.timezone('America/New_York')
        self.israel_tz = pytz.timezone('Asia/Jerusalem')
        self.batch_size = 16  # Optimized for budget
        
        # Print timezone validation on initialization
        self._print_timezone_validation()
        
        # Physics-based analysis template with skeptical constraints
        self.sentiment_template = ChatPromptTemplate.from_template("""
You are a Skeptical Market-Aware Opening Gap Predictor. Your MISSION: Calculate realistic Forward-Looking Gravitational Force with STRICT SKEPTICAL CONSTRAINTS to prevent emotional noise.

🧠 SKEPTICAL CONSTRAINTS - MANDATORY FILTERS:

🔍 EXPECTATION DELTA TEST:
Ask: "Does this news provide a SURPRISE compared to what the market already knows?"
- If it's old news, routine announcements, or widely expected → point_score MUST be near 0
- Only NEW information that creates genuine surprise gets meaningful scores
- "NVIDIA continues to grow" = Expected = 0 points
- "NVIDIA beats earnings by 15%" = Surprise = High points

💎 CONCRETE MASS vs. FLUFF FILTER:
ONLY concrete data gets high gravitational_mass:
- Specific numbers, dates, confirmed contracts = High mass (6-10)
- Vague adjectives ("great", "innovative", "promising") = PENALIZED mass (1-3)
- "Strong partnership" = Fluff = Low mass
- "$5B contract signed" = Concrete = High mass

🚨 OUTLIER CAP - EMOTIONAL NOISE DETECTOR:
MAXIMUM point_score range: -10 to +10 (ABSOLUTE LIMIT)
- Previous scores like +72 are "Emotional Noise" and INVALID
- Scores beyond ±10 = Overenthusiastic analysis = NORMALIZE DOWN
- Most routine news should score ±1 to ±3

📰 PRICED-IN DETECTION — MANDATORY NEUTRAL FILTER:
If the article contains language like:
- "Beat estimates but...", "Strong results despite...", "Revenue grew however..."
- "In line with expectations", "As expected", "Already anticipated"
- "Analysts had predicted", "Market consensus was", "Priced in"
→ The market has ALREADY absorbed this news. Score MUST be near 0 (±1 max).
- "Beat earnings by 2%" = Marginal beat = Priced in = 0 to +1
- "Beat earnings by 20%" = Genuine surprise = +5 to +8
- "Strong results despite macro headwinds" = Hedged language = Market uncertain = +1 max

⚔️ MACRO vs. NVDA CONFLICT RESOLUTION:
When Macro is negative but NVDA news is positive:
- Evaluate if Macro pressure can "SUFFOCATE" company signals
- Strong negative macro (market crash) overpowers weak company news
- Weak negative macro allows strong company news to dominate

{batch_content}

📊 REALISTIC SCORING RUBRIC (STRICTLY ENFORCED):

+1 to +3: Routine positive news (Price-in likely, minimal opening impact)
+4 to +7: Significant surprise or catalyst (Real opening momentum potential)
+8 to +10: Major structural shift (Earnings beat, new GPU architecture, acquisitions)

-1 to -3: Routine negative news (Minor opening pressure)
-4 to -7: Significant negative catalyst (Real opening gap down risk)
-8 to -10: Major negative shock (Earnings miss, regulatory problems, leadership crisis)

CRITICAL RULES:
1. DEFAULT to SKEPTICISM - most news is already priced in
2. PENALIZE vague language heavily
3. REWARD concrete data and genuine surprises
4. NEVER exceed ±10 point_score range
5. Consider market context and expectation baseline

Return ONLY a JSON array with this EXACT format:
[
  {{
    "id": "article_id",
    "point_score": 2.1,
    "sentiment_range": {{
      "min": 1.2,
      "max": 3.0
    }},
    "gravitational_mass": 4.2,
    "entropy": 0.35,
    "reasoning": "Routine positive analyst comment - minimal surprise factor, likely already priced in"
  }}
]

FINAL VALIDATION:
- Does this score reflect realistic market impact?
- Is this news actually surprising?
- Am I being skeptical enough?

Return ONLY the JSON array, no additional text.
""")
    
    def _print_timezone_validation(self):
        """Print timezone validation for temporal physics accuracy"""
        now_utc = datetime.now(pytz.UTC)
        now_israel = now_utc.astimezone(self.israel_tz)
        now_ny = now_utc.astimezone(self.ny_tz)
        
        # Determine active trading day (current NY date)
        active_trading_day = now_ny.strftime('%Y-%m-%d')
        
        print(f"⚛️  TEMPORAL PHYSICS VALIDATION:")
        print(f"   Israel Time:         {now_israel.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"   Market Time (NY):    {now_ny.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"   Active Trading Day:  {active_trading_day}")
        print()
        
        logger.info(f"Temporal Physics - Israel: {now_israel} | NY: {now_ny} | Trading Day: {active_trading_day}")
    
    def get_ny_trading_date(self) -> str:
        """Get current trading date in New York timezone"""
        ny_now = datetime.now(self.ny_tz)
        return ny_now.strftime('%Y-%m-%d')
        
    def analyze_articles_by_type(self, company_articles: List[Dict], macro_articles: List[Dict]) -> Dict:
        """
        Analyze company and macro articles separately and combine results
        
        Args:
            company_articles: List of NVIDIA-specific articles
            macro_articles: List of market/macro articles
            
        Returns:
            Combined sentiment analysis results with individual article details
        """
        logger.info(f"Analyzing {len(company_articles)} company + {len(macro_articles)} macro articles")
        
        # Combine all articles for temporal physics analysis
        all_articles = company_articles + macro_articles
        all_results = self.analyze_all_news_optimized(all_articles, self.get_ny_trading_date())
        
        # Separate results by type
        company_results = []
        macro_results = []
        
        # Map results back to article types
        for i, result in enumerate(all_results):
            if i < len(company_articles):
                company_results.append(result)
                # Save individual sentiment score to article for database storage
                if i < len(company_articles):
                    company_articles[i]['sentiment_score'] = result.get('point_score', 0.0)
            else:
                macro_results.append(result)
                # Save individual sentiment score to article for database storage
                macro_index = i - len(company_articles)
                if macro_index < len(macro_articles):
                    macro_articles[macro_index]['sentiment_score'] = result.get('point_score', 0.0)
        
        # 🏆 GOLDEN CALIBRATION - 65/35 Weighting Rule Implementation
        # Calculate aggregate scores with enhanced weighting
        company_sentiment = self._calculate_weighted_score(company_results, 'company')
        macro_sentiment = self._calculate_weighted_score(macro_results, 'macro')
        
        # Apply the Golden Constant: 65% Company, 35% Macro
        combined_score = (company_sentiment * 0.65) + (macro_sentiment * 0.35)
        
        # 📏 FINAL NORMALIZATION: Ensure combined score stays in [-10, +10]
        combined_score = max(-10.0, min(10.0, combined_score))
        
        logger.info(f"⚡ GOLDEN CALIBRATION: Company {company_sentiment:.2f} (65%) + Macro {macro_sentiment:.2f} (35%) = Combined {combined_score:.2f}")
        
        # Calculate confidence
        combined_confidence = "High" if len(all_results) >= 4 else "Medium" if len(all_results) >= 2 else "Low"
        
        # Extract key factors
        company_factors = self._extract_key_factors(company_results)
        macro_factors = self._extract_key_factors(macro_results)
        
        # Aggregate sentiment_range and entropy from individual articles
        combined_range, combined_entropy = self._aggregate_range_and_entropy(all_results)
        
        logger.info(f"📏 Combined Range: {combined_range} | Entropy: {combined_entropy}")
        
        return {
            "company_sentiment": company_sentiment,
            "macro_sentiment": macro_sentiment,
            "combined_score": combined_score,
            "combined_confidence": combined_confidence,
            "company_confidence": "High" if len(company_results) >= 2 else "Medium",
            "macro_confidence": "High" if len(macro_results) >= 2 else "Medium",
            "company_factors": company_factors,
            "macro_factors": macro_factors,
            "article_count": {"company": len(company_results), "macro": len(macro_results)},
            "individual_results": all_results,
            "combined_range": combined_range,
            "combined_entropy": combined_entropy
        }
    
    def _aggregate_range_and_entropy(self, results: List[Dict]) -> tuple:
        """
        Aggregate sentiment_range and entropy from individual article results.
        
        Takes the min of all mins and max of all maxs to get the combined range,
        then averages entropy values and converts to Low/Medium/High.
        
        Args:
            results: List of individual article analysis results
            
        Returns:
            Tuple of (combined_range_string, entropy_level)
        """
        if not results:
            return "0 to 0", "Low"
        
        all_mins = []
        all_maxs = []
        all_entropy = []
        
        for r in results:
            # Extract sentiment_range (could be dict {min, max} or missing)
            sr = r.get('sentiment_range', {})
            if isinstance(sr, dict):
                if 'min' in sr and 'max' in sr:
                    try:
                        all_mins.append(float(sr['min']))
                        all_maxs.append(float(sr['max']))
                    except (ValueError, TypeError):
                        pass
            
            # Extract entropy (float 0-1)
            ent = r.get('entropy', None)
            if ent is not None:
                try:
                    all_entropy.append(float(ent))
                except (ValueError, TypeError):
                    pass
        
        # Build combined range string
        if all_mins and all_maxs:
            range_min = min(all_mins)
            range_max = max(all_maxs)
            combined_range = f"{range_min:+.1f} to {range_max:+.1f}"
        else:
            combined_range = "0 to 0"
        
        # Calculate average entropy and convert to level
        if all_entropy:
            avg_entropy = sum(all_entropy) / len(all_entropy)
            if avg_entropy >= 0.6:
                entropy_level = "High"
            elif avg_entropy >= 0.3:
                entropy_level = "Medium"
            else:
                entropy_level = "Low"
        else:
            entropy_level = "Low"
        
        return combined_range, entropy_level
        
    def analyze_all_news_optimized(self, articles: List[Dict], prediction_date: str) -> List[Dict]:
        """
        Analyze all news articles with temporal physics applied.
        
        Args:
            articles: List of article dictionaries
            prediction_date: Date for prediction context
            
        Returns:
            List of sentiment analysis results with temporal physics applied
        """
        if not articles:
            logger.info("No articles to analyze")
            return []

        logger.info(f"Starting temporal physics analysis for {len(articles)} articles")
        
        # Apply temporal physics to all articles
        temporal_articles = self._apply_temporal_physics(articles)
        
        # Process in optimized batches
        all_results = []
        total_batches = (len(temporal_articles) + self.batch_size - 1) // self.batch_size
        
        for i in range(0, len(temporal_articles), self.batch_size):
            batch_num = i // self.batch_size + 1
            batch_articles = temporal_articles[i:i + self.batch_size]
            
            logger.info(f"Processing temporal batch {batch_num}/{total_batches} with {len(batch_articles)} articles")
            
            try:
                batch_results = self._process_temporal_batch(batch_articles, prediction_date)
                if batch_results:
                    all_results.extend(batch_results)
                    logger.info(f"Temporal batch {batch_num} completed successfully")
                else:
                    logger.warning(f"Temporal batch {batch_num} returned no results")
            except Exception as e:
                logger.error(f"Error processing temporal batch {batch_num}: {str(e)}")
                continue
                
        logger.info(f"Temporal physics analysis completed: {len(all_results)} articles analyzed")
        return all_results
        
    def _apply_temporal_physics(self, articles: List[Dict]) -> List[Dict]:
        """Apply temporal physics with strict NY timezone reference to avoid timezone paradoxes."""
        temporal_articles = []
        
        # STRICT NY TIMEZONE REFERENCE:
        # Get current NY time (primary reference for all financial calculations)
        ny_now = datetime.now(self.ny_tz)
        
        # Convert to UTC for precise calculations
        ny_now_utc = ny_now.astimezone(pytz.UTC)
        
        # Print validation for every temporal physics run
        israel_now = datetime.now(self.israel_tz)
        trading_day = ny_now.strftime('%Y-%m-%d')
        
        print(f"⏰ TEMPORAL PHYSICS EXECUTION:")
        print(f"   Israel Time:         {israel_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"   Market Time (NY):    {ny_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"   Active Trading Day:  {trading_day}")
        print()
        
        logger.info(f"Temporal Physics Analysis: NY Time = {ny_now} | UTC = {ny_now_utc}")
        
        # First classify all articles for proper Company vs Macro identification
        classification_stats = self._classify_articles(articles)
        
        for article in articles:
            temporal_article = article.copy()
            
            # CONTENT HEALTH CHECK - Use available content but prefer titles+snippets for analysis
            content = article.get('summary', '') or article.get('snippet', '') or article.get('content', '')
            title = article.get('title', '')
            
            # Use full_content first, then fallback to summary/snippet
            full_content = article.get('full_content', '')
            if not full_content:
                full_content = article.get('summary', '') or article.get('snippet', '') or article.get('content', '')
            
            # Use title+content for analysis (titles are usually informative)
            full_text = f"{title}. {full_content}" if full_content else title
            
            if len(full_text) < 20:  # Only skip if virtually no information
                logger.warning(f"Article {article.get('id', 'unknown')} flagged: No meaningful content (<20 chars)")
                continue  # Skip completely empty articles
            
            # Calculate news age with NY timezone reference
            news_age_hours = self._calculate_news_age_utc(article, ny_now_utc)
            temporal_article['news_age_hours'] = news_age_hours
            
            # Apply decay factor - fresh news should stay strong
            decay_factor = 1.0
            if news_age_hours > 12:  # Decay after 12 hours
                decay_factor = 0.7  # 30% decay for older news
                
            temporal_article['decay_factor'] = decay_factor
            
            # Check for post-market timing (after 4:00 PM NY)
            is_post_market = ny_now.hour >= 16
            temporal_article['is_post_market'] = is_post_market
            temporal_article['gap_force_potential'] = is_post_market
            
            temporal_articles.append(temporal_article)
            
        return temporal_articles
        
    def _calculate_news_age_utc(self, article: Dict, mock_time_utc: datetime) -> float:
        """Calculate news age using UTC normalization to eliminate timezone paradoxes."""
        try:
            # Parse article timestamp
            article_time = self._parse_article_timestamp(article)
            if not article_time:
                return 24.0  # Default to 24 hours if timestamp unclear
            
            # CRITICAL UTC ALIGNMENT:
            # Convert article time to UTC
            if article_time.tzinfo is None:
                # Assume naive timestamps are in NY timezone
                article_time = self.ny_tz.localize(article_time)
            article_time_utc = article_time.astimezone(pytz.UTC)
            
            # Calculate age in UTC (eliminates timezone paradoxes)
            # Age = Mock_UTC - Article_UTC
            age_delta = mock_time_utc - article_time_utc
            age_hours = age_delta.total_seconds() / 3600
            
            # TEMPORAL PHYSICS FIX: If negative (future article), set to 0.1h (fresh news)
            if age_hours < 0:
                logger.info(f"Future article detected, setting age to 0.1h for fresh news treatment")
                return 0.1  # Fresh news = 1.0 Decay Factor
            
            return age_hours
            
        except Exception as e:
            logger.error(f"Error calculating UTC age: {str(e)}")
            return 12.0  # Default fallback
    
    def _calculate_news_age(self, article: Dict, ny_now: datetime) -> float:
        """Calculate the age of news article in hours using UTC normalization."""
        try:
            # Parse article timestamp
            article_time = self._parse_article_timestamp(article)
            if not article_time:
                return 24.0  # Default to 24 hours if timestamp unclear
            
            # UNIVERSAL TIME NORMALIZATION - Convert both times to UTC
            # Convert article time to UTC
            if article_time.tzinfo is None:
                # Assume naive timestamps are in NY timezone
                article_time = self.ny_tz.localize(article_time)
            article_time_utc = article_time.astimezone(pytz.UTC)
            
            # Convert mock/current time to UTC  
            if ny_now.tzinfo is None:
                ny_now = self.ny_tz.localize(ny_now)
            mock_time_utc = ny_now.astimezone(pytz.UTC)
            
            # Calculate age in UTC (eliminates timezone paradoxes)
            age_delta = mock_time_utc - article_time_utc
            age_hours = age_delta.total_seconds() / 3600
            
            # TEMPORAL PHYSICS FIX: Ensure positive age, set minimum 0.1h if negative
            if age_hours < 0:
                return 0.1  # Avoid negative time paradox
            
            return age_hours
            
        except Exception as e:
            logger.warning(f"Error calculating news age: {str(e)}")
            return 24.0  # Default fallback
            
    def _classify_articles(self, articles: List[Dict]) -> Dict[str, int]:
        """Classify articles as Company vs Macro with enhanced NVIDIA detection."""
        company_count = 0
        macro_count = 0
        
        # Enhanced NVIDIA keywords for accurate classification
        nvidia_keywords = [
            'nvidia', 'nvda', 'jensen huang', 'gpu', 'h100', 'blackwell',
            'hopper', 'ada lovelace', 'geforce', 'quadro', 'tesla card',
            'cuda', 'omniverse', 'nvi da', 'n v i d a'  # Handle spacing variations
        ]
        
        for article in articles:
            # Combine title, summary, and content for classification
            full_text = (
                article.get('title', '') + ' ' +
                article.get('summary', '') + ' ' +
                article.get('content', '')
            ).lower()
            
            # Check for NVIDIA/Company keywords
            is_company = any(keyword in full_text for keyword in nvidia_keywords)
            
            if is_company:
                company_count += 1
                article['article_type'] = 'company'
            else:
                macro_count += 1
                article['article_type'] = 'macro'
        
        logger.info(f"Article Classification: {company_count} Company, {macro_count} Macro")
        print(f"📊 ARTICLE CLASSIFICATION: {company_count} Company, {macro_count} Macro")
        
        return {'company': company_count, 'macro': macro_count}

    def _parse_article_timestamp(self, article: Dict) -> Optional[datetime]:
        """Parse article timestamp from various possible fields."""
        timestamp_fields = ['published_time', 'publish_date', 'date', 'timestamp', 'created_at']
        
        for field in timestamp_fields:
            if field in article and article[field]:
                try:
                    timestamp_value = article[field]
                    
                    # If it's already a datetime object, return it
                    if isinstance(timestamp_value, datetime):
                        return timestamp_value
                    
                    # If it's a string, try to parse it
                    timestamp_str = str(timestamp_value)
                    
                    # Try common timestamp formats
                    formats = [
                        '%Y-%m-%d %H:%M:%S',
                        '%Y-%m-%d %H:%M:%S.%f',
                        '%Y-%m-%dT%H:%M:%S',
                        '%Y-%m-%dT%H:%M:%S.%f',
                        '%Y-%m-%dT%H:%M:%SZ',
                        '%Y-%m-%d',
                    ]
                    
                    for fmt in formats:
                        try:
                            return datetime.strptime(timestamp_str, fmt)
                        except ValueError:
                            continue
                            
                except Exception:
                    continue
                    
        return None
        
    def _process_temporal_batch(self, batch_articles: List[Dict], prediction_date: str) -> List[Dict]:
        """Process a batch of articles with temporal physics."""
        try:
            # Prepare temporal batch content
            batch_content = self._prepare_batch_content_temporal(batch_articles)
            
            # Create temporal prompt
            prompt = self.sentiment_template.format(batch_content=batch_content)
            
            # Get AI response
            response = self._query_ai(prompt)
            
            if not response:
                logger.error("No response from AI for temporal batch")
                return []
                
            # Parse temporal response
            parsed_results = self._parse_batch_response_temporal(response, batch_articles)
            
            return parsed_results
            
        except Exception as e:
            logger.error(f"Error processing temporal batch: {str(e)}")
            return []
            
    def _prepare_batch_content_temporal(self, articles: List[Dict]) -> str:
        """Prepare batch content with temporal physics and enhanced classification."""
        # First classify all articles
        classification_stats = self._classify_articles(articles)
        
        content_parts = []
        
        for i, article in enumerate(articles, 1):
            # Get temporal data
            news_age = article.get('news_age_hours', 24)
            decay_factor = article.get('decay_factor', 1.0)
            is_post_market = article.get('is_post_market', False)
            
            # Get article type from enhanced classification
            article_type = article.get('article_type', 'macro')
            
            # 🚀 NO DATA LEFT BEHIND POLICY - Enhanced Content Fallback Strategy
            # Priority: full_content > summary > snippet > content > title (NEVER NULL)
            content = article.get('full_content', '') or article.get('summary', '') or article.get('snippet', '') or article.get('content', '')
            title = article.get('title', 'No title')
            
            # CRITICAL MASS PRESERVATION: Title contains the 'Critical Mass' of news
            # If NO content available, title becomes the primary analysis text
            if content:
                # Full content available: Title + Content
                combined_content = f"{title}. {content}"
            else:
                # No content: Title becomes the ONLY analysis source
                combined_content = title
                logger.warning(f"No content available for article, using title as primary text: {title[:100]}...")
            
            # MANDATORY: Always ensure we have SOME text to analyze
            if not combined_content.strip():
                combined_content = "Market news update - analyzing sentiment impact"
                logger.warning(f"Article had completely empty content, using fallback text")
                
            content_preview = combined_content[:500] if len(combined_content) > 50 else combined_content
            
            article_content = f"""
Article {i} (ID: {article.get('id', f'article_{i}')}): 
Title: {title}
Content: {content_preview}
Source: {article.get('source', 'Unknown')}
Age: {news_age:.1f} hours (Decay: {decay_factor:.1f}x)
Type: {article_type.upper()}
Post-Market: {'YES - Gap Force Potential' if is_post_market else 'NO'}
Content Length: {len(combined_content)} chars (Full Content: {'YES' if article.get('full_content') else 'NO'})
"""
            content_parts.append(article_content.strip())
            
        return "\n\n".join(content_parts)
        
    def _is_macro_article(self, article: Dict) -> bool:
        """Determine if article is macro-economic news."""
        macro_keywords = [
            'federal reserve', 'fed', 'inflation', 'gdp', 'unemployment',
            'interest rate', 'monetary policy', 'fiscal policy', 'recession',
            'economic data', 'cpi', 'ppi', 'jobs report', 'fomc'
        ]
        
        text_to_check = (
            article.get('title', '') + ' ' + 
            article.get('content', '')
        ).lower()
        
        return any(keyword in text_to_check for keyword in macro_keywords)
        
    def _parse_batch_response_temporal(self, response: str, articles: List[Dict]) -> List[Dict]:
        """Parse AI response for temporal batch analysis."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\[[\s\S]*\]', response)
            if not json_match:
                logger.error("No JSON array found in AI response")
                return []
                
            json_str = json_match.group(0)
            analysis_results = json.loads(json_str)
            
            if not isinstance(analysis_results, list):
                logger.error("AI response is not a JSON array")
                return []
                
            # Apply temporal physics to results
            temporal_results = []
            
            for i, result in enumerate(analysis_results):
                if i < len(articles):
                    article = articles[i]
                    temporal_result = result.copy()
                    
                    # Apply decay factor to gravitational mass
                    decay_factor = article.get('decay_factor', 1.0)
                    original_mass = result.get('gravitational_mass', 5.0)
                    decayed_mass = original_mass * decay_factor
                    temporal_result['gravitational_mass'] = decayed_mass
                    
                    # Apply dynamic macro weighting if mass >= 9
                    is_macro = self._is_macro_article(article)
                    if is_macro and decayed_mass >= 9.0:
                        temporal_result['macro_weight'] = 0.7
                        temporal_result['company_weight'] = 0.3
                        temporal_result['dynamic_weighting'] = True
                    else:
                        temporal_result['macro_weight'] = 0.5
                        temporal_result['company_weight'] = 0.5
                        temporal_result['dynamic_weighting'] = False
                        
                    # Add temporal metadata + source for tier-weighted scoring
                    temporal_result['news_age_hours'] = article.get('news_age_hours', 24)
                    temporal_result['decay_factor'] = decay_factor
                    temporal_result['is_post_market'] = article.get('is_post_market', False)
                    temporal_result['gap_force_potential'] = article.get('gap_force_potential', False)
                    temporal_result['source'] = article.get('source', '')
                    
                    temporal_results.append(temporal_result)
                    
            return temporal_results
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error parsing temporal batch response: {str(e)}")
            return []
            
    def _query_ai(self, prompt: str) -> str:
        """Query the AI model with the given prompt."""
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.llm.invoke(messages)
            
            if hasattr(response, 'content'):
                return response.content
            elif isinstance(response, str):
                return response
            else:
                logger.error(f"Unexpected response type: {type(response)}")
                return ""
                
        except Exception as e:
            logger.error(f"Error querying AI: {str(e)}")
            return ""

    def analyze_sentiment(self, title: str, content: str, source: str = "") -> Dict:
        """
        Legacy method for single article analysis - now with temporal physics
        """
        article = {
            'id': 'single_article',
            'title': title,
            'content': content,
            'source': source,
            'published_time': datetime.now()
        }
        
        results = self.analyze_all_news_optimized([article], str(datetime.now().date()))
        
        if results:
            return results[0]
        else:
            # Fallback result
            return {
                'sentiment_range': {'min': -1.0, 'max': 1.0},
                'gravitational_mass': 3.0,
                'entropy': 0.5,
                'reasoning': 'Fallback analysis due to processing error'
            }
    
    def _calculate_weighted_score(self, results: List[Dict], article_type: str) -> float:
        """
        Calculate tier-weighted average sentiment score.
        
        Uses source tier weights instead of raw summation to prevent Volume Bias.
        Includes Black Swan Protection: articles with score < -8 get doubled weight.
        Final result is clamped to [-10, +10] for parity with Technical Score.
        
        Tier Weights:
            Tier 1 (Bloomberg, Reuters, etc.): 1.5
            Tier 2 (Seeking Alpha, CNBC, etc.): 1.0
            Tier 3 / Unknown: 0.7
        
        Args:
            results: List of sentiment analysis results
            article_type: 'company' or 'macro'
            
        Returns:
            Weighted average sentiment score, clamped to [-10, +10]
        """
        if not results:
            return 0.0
        
        # Tier weight mapping
        TIER_WEIGHTS = {1: 1.5, 2: 1.0, 3: 0.7, 0: 0.5}
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for result in results:
            base_score = result.get('point_score', 0.0)
            source = result.get('source', '') or ''
            
            # Get tier weight from trusted_sources config
            tier = get_source_tier(source)
            tier_weight = TIER_WEIGHTS.get(tier, 0.7)
            
            # 🎯 Macro Noise Filtering: Reduce weak macro signals
            if article_type == 'macro' and -0.2 <= base_score <= 0.2:
                tier_weight *= 0.5
                logger.debug(f"Macro noise filtering: {base_score:.2f} in [-0.2, +0.2] → Weight halved")
            
            # 🦢 BLACK SWAN PROTECTION: Double weight for catastrophic news (score < -8)
            if base_score < -8:
                tier_weight *= 2.0
                logger.info(f"🦢 Black Swan detected: score={base_score:.1f}, source={source} → Weight doubled to {tier_weight:.1f}")
            
            weighted_sum += base_score * tier_weight
            total_weight += tier_weight
            
            logger.debug(f"{article_type.capitalize()} article [{source}] Tier {tier}: score={base_score:.2f} × weight={tier_weight:.1f}")
        
        if total_weight == 0:
            return 0.0
        
        # Weighted average (NOT sum!) — prevents Volume Bias
        weighted_avg = weighted_sum / total_weight
        
        # 📏 NORMALIZATION: Clamp to [-10, +10] to match Technical Score range
        clamped = max(-10.0, min(10.0, weighted_avg))
        
        logger.info(f"📊 {article_type.capitalize()} Score: avg={weighted_avg:.2f} → clamped={clamped:.2f} (from {len(results)} articles, total_weight={total_weight:.1f})")
        
        return clamped
    
    def _calculate_average_score(self, results: List[Dict]) -> float:
        """Legacy method - kept for backward compatibility"""
        if not results:
            return 0.0
        
        scores = [result.get('point_score', 0.0) for result in results]
        return sum(scores) / len(scores)
    
    def _extract_key_factors(self, results: List[Dict]) -> str:
        """Extract key factors from sentiment analysis results"""
        if not results:
            return "No articles analyzed"
        
        factors = []
        for result in results:
            reasoning = result.get('reasoning', '')
            if reasoning:
                # Extract first sentence as key factor
                first_sentence = reasoning.split('.')[0]
                if first_sentence:
                    factors.append(first_sentence)
        
        return '; '.join(factors[:3]) if factors else "General market sentiment"