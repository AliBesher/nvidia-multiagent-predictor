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
from utils.logger import setup_logger
import re

logger = setup_logger(__name__)

class SentimentAgent(BaseAgent):
    """
    Agent for analyzing sentiment from news articles using GPT-4 with Temporal Physics.
    Implements time-based decay for news aging, dynamic weighting, and post-market awareness.
    """
    
    def __init__(self):
        super().__init__("SentimentAgent")
        self.ny_tz = pytz.timezone('America/New_York')
        self.batch_size = 16  # Optimized for budget
        
        # Physics-based analysis template
        self.sentiment_template = ChatPromptTemplate.from_template("""
You are a Data Physics Analyst. Treat each news article as an informational gravity object with mass, sentiment range, and entropy.

{batch_content}

Analyze each article and return ONLY a JSON array with this exact format:
[
  {{
    "id": "news_id",
    "sentiment_range": {{
      "min": -10.0,
      "max": 10.0
    }},
    "gravitational_mass": 8.5,
    "entropy": 0.75,
    "reasoning": "Brief analysis explaining the physics"
  }}
]

Physics Rules:
1. Sentiment Range: Use the full -10 to +10 scale
2. Gravitational Mass: 1-10 scale (importance/market impact)
3. Entropy: 0-1 scale (uncertainty/chaos in information)
4. Temporal Decay: Already applied to mass values
5. Post-Market: Gap force potential noted in reasoning

Return ONLY the JSON array, no additional text.
""")

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
        """Apply temporal physics calculations to articles."""
        ny_now = datetime.now(self.ny_tz)
        temporal_articles = []
        
        for article in articles:
            temporal_article = article.copy()
            
            # Calculate news age
            news_age_hours = self._calculate_news_age(article, ny_now)
            temporal_article['news_age_hours'] = news_age_hours
            
            # Apply decay factor for articles > 12 hours old
            decay_factor = 1.0
            if news_age_hours > 12:
                decay_factor = 0.7  # 30% decay
                
            temporal_article['decay_factor'] = decay_factor
            
            # Check for post-market timing (after 4:00 PM NY)
            is_post_market = ny_now.hour >= 16
            temporal_article['is_post_market'] = is_post_market
            temporal_article['gap_force_potential'] = is_post_market
            
            temporal_articles.append(temporal_article)
            
        return temporal_articles
        
    def _calculate_news_age(self, article: Dict, ny_now: datetime) -> float:
        """Calculate the age of news article in hours."""
        try:
            # Parse article timestamp
            article_time = self._parse_article_timestamp(article)
            if not article_time:
                return 24.0  # Default to 24 hours if timestamp unclear
                
            # Convert to NY timezone for comparison
            if article_time.tzinfo is None:
                article_time = self.ny_tz.localize(article_time)
            else:
                article_time = article_time.astimezone(self.ny_tz)
                
            # Calculate age in hours
            age_delta = ny_now - article_time
            age_hours = age_delta.total_seconds() / 3600
            
            return max(0, age_hours)  # Ensure non-negative
            
        except Exception as e:
            logger.warning(f"Error calculating news age: {str(e)}")
            return 24.0  # Default fallback
            
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
        """Prepare batch content with temporal physics information."""
        content_parts = []
        
        for i, article in enumerate(articles, 1):
            # Get temporal data
            news_age = article.get('news_age_hours', 24)
            decay_factor = article.get('decay_factor', 1.0)
            is_post_market = article.get('is_post_market', False)
            
            # Determine if this is a macro article for dynamic weighting
            is_macro = self._is_macro_article(article)
            
            article_content = f"""
Article {i} (ID: {article.get('id', f'article_{i}')}):
Title: {article.get('title', 'No title')}
Content: {article.get('content', 'No content')[:500]}...
Source: {article.get('source', 'Unknown')}
Age: {news_age:.1f} hours (Decay: {decay_factor:.1f}x)
Type: {'MACRO' if is_macro else 'COMPANY'}
Post-Market: {'YES - Gap Force Potential' if is_post_market else 'NO'}
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
                        
                    # Add temporal metadata
                    temporal_result['news_age_hours'] = article.get('news_age_hours', 24)
                    temporal_result['decay_factor'] = decay_factor
                    temporal_result['is_post_market'] = article.get('is_post_market', False)
                    temporal_result['gap_force_potential'] = article.get('gap_force_potential', False)
                    
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