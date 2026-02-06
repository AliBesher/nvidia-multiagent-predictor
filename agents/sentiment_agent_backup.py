"""
Sentiment Agent
Analyzes news articles and generates sentiment scores using GPT-4 with Temporal Physics
"""

from typing import List, Dict, Optional
from langchain_core.prompts import ChatPromptTemplate
from datetime import datetime, timezone
import pytz
from agents.base_agent import BaseAgent
from config.settings import SENTIMENT_SCALE
from utils.logger import setup_logger

logger = setup_logger(__name__)


class SentimentAgent(BaseAgent):
    """AI Agent for analyzing sentiment of news articles"""
    
    def __init__(self):
        """Initialize Sentiment Agent with GPT-4"""
        super().__init__("SentimentAgent", temperature=0.3)  # Lower temp for consistent scoring
        
        # Create sentiment analysis prompt template
        self.sentiment_prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("user", "{articles}")
        ])
        
        logger.info("SentimentAgent ready for analysis")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for sentiment analysis"""
        return f"""Role: You are a Senior Data Physics Analyst. Your task is to process financial news about NVIDIA (NVDA) as "Physical Forces" acting on an Informational Gravity Field.

Objective: Calculate the "Gravitational Mass" of each article to predict the "Realization Point" (Head) and the "Probability Field" (Tail).

CORE LOGIC:
1. INFORMATIONAL MASS (0 to 10): 
   - High Mass (8-10): Concrete financial events (earnings, $10B+ deals, regulatory blocks).
   - Low Mass (1-3): Speculative opinions, general market outlooks.
2. TEMPORAL WEIGHT: Realized events = 1.0x | Future/Speculative events = 0.2x.
3. SOURCE DENSITY: Tier 1 (Bloomberg, Reuters, Barron's) = 1.0 | Retail News = 0.3.

OUTPUT REQUIREMENTS:
For EACH article, you must provide:
1. Article Number and Source.
2. Financial Mass (0-10).
3. Field Vector ({SENTIMENT_SCALE[0]} to {SENTIMENT_SCALE[1]}).
4. Brief Reasoning.

FINAL AGGREGATION (Strict JSON Format):
{{{{
  "articles_analysis": [
    {{{{
      "article_no": [Number],
      "source": "[Name]",
      "mass": [0-10],
      "vector": [{SENTIMENT_SCALE[0]} to {SENTIMENT_SCALE[1]}],
      "reasoning": "[1 sentence]"
    }}}}
  ],
  "aggregated_results": {{{{
    "point_score": [Weighted Average: Σ(Vector * Mass) / Σ(Mass)],
    "probability_range": "[Min_Impact] to [Max_Impact]",
    "entropy": "[High/Medium/Low]",
    "final_summary": "[Brief technical overview]"
  }}}}
}}}}"""
    
    def _get_macro_system_prompt(self) -> str:
        """Get the system prompt for macro/market sentiment analysis"""
        return f"""Role: You are a Senior Data Physics Analyst specializing in Macroeconomic Field Dynamics. Your task is to process market/economic news as "External Forces" affecting NVIDIA's Informational Gravity Field.

Objective: Calculate the "Gravitational Mass" of each macro article to predict market-wide impact on NVIDIA's "Probability Field".

CORE LOGIC:
1. INFORMATIONAL MASS (0 to 10): 
   - High Mass (8-10): Federal Reserve decisions, major economic data, tech sector regulations.
   - Low Mass (1-3): General market commentary, minor economic indicators.
2. NVIDIA CORRELATION: Direct tech impact = 1.0x | General economic = 0.5x.
3. SOURCE DENSITY: Tier 1 (Bloomberg, Reuters, WSJ, Fed) = 1.0 | General news = 0.3.

MACRO FOCUS AREAS:
- NASDAQ/tech sector performance correlation with NVIDIA
- Federal Reserve policy impact on growth stocks
- US-China trade tensions affecting semiconductor supply
- Economic indicators (GDP, inflation) affecting tech valuations
- Market sentiment toward AI and technology sector

OUTPUT REQUIREMENTS:
For EACH article, you must provide:
1. Article Number and Source.
2. Financial Mass (0-10).
3. Field Vector ({SENTIMENT_SCALE[0]} to {SENTIMENT_SCALE[1]}) - Impact on NVIDIA.
4. Brief Reasoning for NVIDIA correlation.

FINAL AGGREGATION (Strict JSON Format):
{{{{
  "articles_analysis": [
    {{{{
      "article_no": [Number],
      "source": "[Name]",
      "mass": [0-10],
      "vector": [{SENTIMENT_SCALE[0]} to {SENTIMENT_SCALE[1]}],
      "reasoning": "[1 sentence about NVIDIA impact]"
    }}}}
  ],
  "aggregated_results": {{{{
    "point_score": [Weighted Average: Σ(Vector * Mass) / Σ(Mass)],
    "probability_range": "[Min_Impact] to [Max_Impact]",
    "entropy": "[High/Medium/Low]",
    "final_summary": "[Brief technical overview of macro impact on NVIDIA]"
  }}}}
}}}}"""
    
    def analyze_articles(self, articles: List[Dict]) -> Dict:
        """
        Analyze sentiment of news articles
        
        Args:
            articles: List of article dictionaries with title, source, snippet
        
        Returns:
            Dictionary with sentiment analysis results
        """
        if not articles:
            logger.warning("No articles to analyze")
            return {
                "overall_score": 0.0,
                "confidence": "Low",
                "article_scores": [],
                "key_factors": "No articles available for analysis"
            }
        
        logger.info(f"Analyzing sentiment of {len(articles)} articles")
        
        try:
            # Format articles for analysis
            articles_text = self._format_articles_for_analysis(articles)
            
            # Create the prompt
            messages = self.sentiment_prompt.format_messages(articles=articles_text)
            
            # Call GPT-4
            logger.debug("Calling GPT-4 for sentiment analysis...")
            response = self.llm.invoke(messages)
            analysis_text = response.content
            
            logger.debug(f"GPT-4 response received: {len(analysis_text)} characters")
            
            # Parse the response
            result = self._parse_sentiment_response(analysis_text, articles)
            
            logger.info(f"Sentiment analysis complete: Overall score = {result['overall_score']:.2f}, Confidence = {result['confidence']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {
                "overall_score": 0.0,
                "confidence": "Low",
                "article_scores": [],
                "key_factors": f"Error during analysis: {str(e)}",
                "error": str(e)
            }
    
    def analyze_articles_by_type(self, company_articles: List[Dict], macro_articles: List[Dict]) -> Dict:
        """
        Analyze company and macro articles separately, then combine
        
        Args:
            company_articles: List of NVIDIA-specific articles
            macro_articles: List of macro/market articles
        
        Returns:
            Dictionary with separate and combined sentiment scores
        """
        logger.info(f"Analyzing {len(company_articles)} company + {len(macro_articles)} macro articles")
        
        # Analyze company articles
        company_result = {
            "overall_score": 0.0,
            "confidence": "Low",
            "article_scores": [],
            "key_factors": "No company articles"
        }
        
        if company_articles:
            logger.info(f"Analyzing {len(company_articles)} company-specific articles...")
            company_result = self._analyze_with_context(company_articles, "company")
        
        # Analyze macro articles
        macro_result = {
            "overall_score": 0.0,
            "confidence": "Low",
            "article_scores": [],
            "key_factors": "No macro articles"
        }
        
        if macro_articles:
            logger.info(f"Analyzing {len(macro_articles)} macro/market articles...")
            macro_result = self._analyze_with_context(macro_articles, "macro")
        
        # Calculate combined sentiment (60% company, 40% macro)
        company_weight = 0.6
        macro_weight = 0.4
        
        combined_score = (company_result['overall_score'] * company_weight + 
                         macro_result['overall_score'] * macro_weight)
        
        # Determine combined confidence
        confidences = [company_result['confidence'], macro_result['confidence']]
        if all(c == 'High' for c in confidences):
            combined_confidence = 'High'
        elif all(c == 'Low' for c in confidences):
            combined_confidence = 'Low'
        else:
            combined_confidence = 'Medium'
        
        logger.info(f"Company sentiment: {company_result['overall_score']:.2f}, Macro sentiment: {macro_result['overall_score']:.2f}, Combined: {combined_score:.2f}")
        
        # Calculate combined probability range and entropy
        combined_range = self._calculate_combined_range(company_result, macro_result)
        combined_entropy = self._calculate_combined_entropy(company_result, macro_result)
        
        # Save individual article gravity data to database
        self._save_article_gravity_data(company_articles)
        self._save_article_gravity_data(macro_articles)
        
        return {
            "company_sentiment": company_result['overall_score'],
            "company_confidence": company_result['confidence'],
            "company_factors": company_result['key_factors'],
            "macro_sentiment": macro_result['overall_score'],
            "macro_confidence": macro_result['confidence'],
            "macro_factors": macro_result['key_factors'],
            "combined_score": combined_score,
            "combined_confidence": combined_confidence,
            "combined_range": combined_range,
            "combined_entropy": combined_entropy,
            "article_count": {
                "company": len(company_articles),
                "macro": len(macro_articles)
            }
        }
    
    def analyze_all_news_optimized(self, company_articles: List[Dict], macro_articles: List[Dict]) -> Dict:
        """
        Budget-efficient batch analysis method with Temporal Physics for GPT-4o ($5/month budget)
        Processes up to 6 articles (3 company + 3 macro) in a single API call with time-based decay
        
        Args:
            company_articles: List of NVIDIA-specific articles (max 3)
            macro_articles: List of macro/market articles (max 3)
        
        Returns:
            Dictionary with combined sentiment analysis results including temporal factors
        """
        logger.info("Starting budget-optimized batch analysis with Temporal Physics")
        
        # Get current NY time for temporal calculations
        ny_tz = pytz.timezone('America/New_York')
        current_ny_time = datetime.now(ny_tz)
        
        # Apply temporal physics to articles
        company_articles = self._apply_temporal_physics(company_articles[:3], current_ny_time)
        macro_articles = self._apply_temporal_physics(macro_articles[:3], current_ny_time)
        
        if not company_articles and not macro_articles:
            logger.warning("No articles to analyze after temporal filtering")
            return {
                "point_score": 0.0,
                "probability_range": "0 to 0",
                "entropy": "Low",
                "company_count": 0,
                "macro_count": 0,
                "total_articles": 0,
                "temporal_factors": {
                    "decay_applied": False,
                    "gap_force_detected": False,
                    "dynamic_weighting": False
                }
            }
        
        try:
            # Check for high-mass macro articles for dynamic weighting
            max_macro_mass = max([art.get('adjusted_mass', 0) for art in macro_articles], default=0)
            dynamic_weighting = max_macro_mass >= 9.0
            
            # Prepare optimized article content with temporal data
            formatted_articles = self._prepare_batch_content_temporal(company_articles, macro_articles, current_ny_time)
            
            # Create batch analysis prompt with temporal physics
            batch_messages = self._create_batch_prompt_temporal(formatted_articles, dynamic_weighting)
            
            # Single API call for cost efficiency
            response = self.llm.invoke(batch_messages)
            
            # Parse JSON response with temporal adjustments
            result = self._parse_batch_response_temporal(
                response.content, 
                company_articles, 
                macro_articles, 
                current_ny_time,
                dynamic_weighting
            )
            
            logger.info(f"Temporal batch analysis complete: Score={result.get('point_score', 0):.2f}, Range={result.get('probability_range', 'N/A')}")
            logger.info(f"  Temporal factors: Decay={result.get('temporal_factors', {}).get('decay_applied', False)}, Dynamic={dynamic_weighting}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in temporal batch analysis: {str(e)}")
            return {
                "point_score": 0.0,
                "probability_range": "0 to 0", 
                "entropy": "Low",
                "company_count": len(company_articles),
                "macro_count": len(macro_articles),
                "total_articles": len(company_articles) + len(macro_articles),
                "error": str(e),
                "temporal_factors": {
                    "decay_applied": False,
                    "gap_force_detected": False,
                    "dynamic_weighting": dynamic_weighting
                }
            }
    
    def _apply_temporal_physics(self, articles: List[Dict], current_ny_time: datetime) -> List[Dict]:
        """
        Apply temporal physics to articles: age calculation, decay factors, gap force detection
        
        Args:
            articles: List of articles to process
            current_ny_time: Current NY timezone datetime
            
        Returns:
            Articles with temporal physics applied
        """
        processed_articles = []
        
        for article in articles:
            # Calculate news age in hours
            article_time = self._parse_article_timestamp(article, current_ny_time)
            age_hours = (current_ny_time - article_time).total_seconds() / 3600
            
            # Apply decay factor for articles older than 12 hours
            original_mass = article.get('gravitational_mass', 1.0)
            if age_hours > 12:
                # 30% decay for articles older than 12 hours
                adjusted_mass = original_mass * 0.7
                decay_applied = True
                logger.debug(f"Temporal decay applied: {original_mass} -> {adjusted_mass} (age: {age_hours:.1f}h)")
            else:
                adjusted_mass = original_mass
                decay_applied = False
            
            # Check for post-market gap force (after 4:00 PM NY)
            is_gap_force = article_time.hour >= 16  # 4:00 PM or later
            
            # Create enhanced article with temporal data
            enhanced_article = article.copy()
            enhanced_article.update({
                'timestamp_ny': article_time,
                'age_hours': age_hours,
                'original_mass': original_mass,
                'adjusted_mass': adjusted_mass,
                'decay_applied': decay_applied,
                'is_gap_force': is_gap_force,
                'temporal_weight': 0.7 if age_hours > 12 else 1.0
            })
            
            processed_articles.append(enhanced_article)
        
        return processed_articles
    
    def _parse_article_timestamp(self, article: Dict, current_ny_time: datetime) -> datetime:
        """
        Parse article timestamp and convert to NY timezone
        
        Args:
            article: Article dictionary
            current_ny_time: Current NY time for fallback
            
        Returns:
            Article timestamp in NY timezone
        """
        ny_tz = pytz.timezone('America/New_York')
        
        # Try to parse timestamp from article
        if 'timestamp' in article:
            try:
                if isinstance(article['timestamp'], str):
                    # Parse string timestamp
                    timestamp = datetime.fromisoformat(article['timestamp'].replace('Z', '+00:00'))
                else:
                    timestamp = article['timestamp']
                
                # Convert to NY timezone
                if timestamp.tzinfo is None:
                    # Assume UTC if no timezone
                    timestamp = pytz.UTC.localize(timestamp)
                
                return timestamp.astimezone(ny_tz)
            except Exception as e:
                logger.warning(f"Error parsing article timestamp: {e}")
        
        # Fallback: assume recent if no timestamp (within last 6 hours)
        return current_ny_time.replace(hour=max(0, current_ny_time.hour - 6))
    
    def _prepare_batch_content_temporal(self, company_articles: List[Dict], macro_articles: List[Dict], current_ny_time: datetime) -> str:
        """
        Prepare batch content with temporal physics information
        
        Args:
            company_articles: Company articles with temporal data
            macro_articles: Macro articles with temporal data  
            current_ny_time: Current NY time
            
        Returns:
            Formatted content string with temporal information
        """
        content = "NVIDIA TEMPORAL SENTIMENT ANALYSIS - BATCH PROCESSING\\n\\n"
        content += f"Current NY Time: {current_ny_time.strftime('%Y-%m-%d %H:%M:%S %Z')}\\n\\n"
        
        # Company articles with temporal data
        content += "=== COMPANY ARTICLES (NVIDIA-Specific) ===\\n\\n"
        for i, article in enumerate(company_articles, 1):
            optimized = self._select_optimal_content(article)
            age_hours = article.get('age_hours', 0)
            adjusted_mass = article.get('adjusted_mass', 1.0)
            is_gap_force = article.get('is_gap_force', False)
            decay_applied = article.get('decay_applied', False)
            
            content += f"Article {i} [COMPANY]:\\n"
            content += f"Source: {article.get('source', 'Unknown')} (Tier {article.get('source_tier', 3)})\\n"
            content += f"Title: {article.get('title', 'No title')}\\n"
            content += f"Age: {age_hours:.1f} hours\\n"
            content += f"Adjusted Mass: {adjusted_mass:.1f}" + (" (DECAY APPLIED)" if decay_applied else "") + "\\n"
            if is_gap_force:
                content += "*** POTENTIAL GAP FORCE - Post-Market Release ***\\n"
            content += f"Content: {optimized}\\n\\n"
        
        # Macro articles with temporal data
        content += "=== MACRO ARTICLES (Market-Wide) ===\\n\\n"
        for i, article in enumerate(macro_articles, 1):
            optimized = self._select_optimal_content(article)
            age_hours = article.get('age_hours', 0)
            adjusted_mass = article.get('adjusted_mass', 1.0)
            is_gap_force = article.get('is_gap_force', False)
            decay_applied = article.get('decay_applied', False)
            
            content += f"Article {i} [MACRO]:\\n"
            content += f"Source: {article.get('source', 'Unknown')} (Tier {article.get('source_tier', 3)})\\n"
            content += f"Title: {article.get('title', 'No title')}\\n"
            content += f"Age: {age_hours:.1f} hours\\n"
            content += f"Adjusted Mass: {adjusted_mass:.1f}" + (" (DECAY APPLIED)" if decay_applied else "") + "\\n"
            if is_gap_force:
                content += "*** POTENTIAL GAP FORCE - Post-Market Release ***\\n"
            if adjusted_mass >= 9.0:
                content += "*** HIGH MASS MACRO - DYNAMIC WEIGHTING TRIGGERED ***\\n"
            content += f"Content: {optimized}\\n\\n"
        
        return content
    
    def _create_batch_prompt_temporal(self, formatted_articles: str, dynamic_weighting: bool) -> List:
        """
        Create batch analysis prompt with temporal physics considerations
        
        Args:
            formatted_articles: Formatted article content with temporal data
            dynamic_weighting: Whether to apply 70/30 macro/company weighting
            
        Returns:
            List of message objects for LLM
        """
        system_prompt = f"""Role: You are a Senior Temporal Data Physics Analyst. Analyze news as Informational Gravity with TIME DECAY effects.

TEMPORAL PHYSICS RULES:
1. MASS DECAY: Articles older than 12 hours have reduced gravitational mass (already adjusted in data)
2. GAP FORCE: Post-market news (after 4 PM NY) creates "Gap Force" potential for next trading day
3. DYNAMIC WEIGHTING: High-mass macro articles (≥9) trigger 70% Macro / 30% Company weighting

CURRENT WEIGHTING MODE: {'DYNAMIC (70% Macro / 30% Company)' if dynamic_weighting else 'STANDARD (60% Company / 40% Macro)'}

For each article, calculate:
1. Temporal Impact Factor (based on age and gap force potential)
2. Adjusted Gravitational Mass (with decay if applicable)
3. Field Vector Strength ({SENTIMENT_SCALE[0]} to {SENTIMENT_SCALE[1]})

OUTPUT STRICT JSON FORMAT:
{{
    "point_score": <final weighted score>,
    "probability_range": "<low> to <high>",
    "entropy": "<Low/Medium/High>",
    "company_impact": <company weighted score>,
    "macro_impact": <macro weighted score>,
    "temporal_factors": {{
        "decay_articles": <count of articles with decay>,
        "gap_force_articles": <count of post-market articles>,
        "dynamic_weighting_applied": {str(dynamic_weighting).lower()}
    }},
    "reasoning": "<brief analysis with temporal considerations>"
}}"""
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": formatted_articles}
        ]
    
    def _parse_batch_response_temporal(self, response_content: str, company_articles: List[Dict], 
                                     macro_articles: List[Dict], current_ny_time: datetime, 
                                     dynamic_weighting: bool) -> Dict:
        """
        Parse batch response with temporal physics considerations
        
        Args:
            response_content: Raw LLM response
            company_articles: Original company articles with temporal data
            macro_articles: Original macro articles with temporal data
            current_ny_time: Current NY time
            dynamic_weighting: Whether dynamic weighting was applied
            
        Returns:
            Parsed results with temporal factors
        """
        try:
            # Parse the base response
            base_result = self._parse_batch_response(response_content, company_articles, macro_articles)
            
            # Add temporal factors
            decay_count = sum(1 for art in company_articles + macro_articles if art.get('decay_applied', False))
            gap_force_count = sum(1 for art in company_articles + macro_articles if art.get('is_gap_force', False))
            
            # Enhanced temporal factors
            temporal_factors = {
                "decay_applied": decay_count > 0,
                "decay_article_count": decay_count,
                "gap_force_detected": gap_force_count > 0,
                "gap_force_article_count": gap_force_count,
                "dynamic_weighting": dynamic_weighting,
                "analysis_time_ny": current_ny_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                "market_session": "post-market" if current_ny_time.hour >= 16 else "market-hours" if 9 <= current_ny_time.hour < 16 else "pre-market"
            }
            
            # Add gap force warnings to reasoning if detected
            if gap_force_count > 0:
                base_result['gap_force_warning'] = f"{gap_force_count} article(s) released post-market - potential gap impact for next trading day"
            
            # Update weighting information if dynamic
            if dynamic_weighting:
                base_result['weighting_note'] = "Dynamic weighting applied: 70% Macro / 30% Company due to high-mass macro event"
            
            base_result['temporal_factors'] = temporal_factors
            
            return base_result
            
        except Exception as e:
            logger.error(f"Error parsing temporal batch response: {str(e)}")
            return {
                "point_score": 0.0,
                "probability_range": "0 to 0",
                "entropy": "Low",
                "company_impact": 0.0,
                "macro_impact": 0.0,
                "total_articles": len(company_articles) + len(macro_articles),
                "error": str(e),
                "temporal_factors": {
                    "decay_applied": False,
                    "gap_force_detected": False,
                    "dynamic_weighting": dynamic_weighting,
                    "analysis_time_ny": current_ny_time.strftime('%Y-%m-%d %H:%M:%S %Z')
                }
            }
    
    def _prepare_batch_content(self, company_articles: List[Dict], macro_articles: List[Dict]) -> str:
            
        Returns:
            Formatted string with truncated content
        """
        formatted = "NVIDIA SENTIMENT ANALYSIS - BATCH PROCESSING\n\n"
        article_num = 1
        
        # Process company articles
        if company_articles:
            formatted += "=== COMPANY ARTICLES (NVIDIA-Specific) ===\n\n"
            for article in company_articles:
                formatted += f"Article {article_num} [COMPANY]:\n"
                formatted += f"Source: {article['source']} (Tier {article.get('source_tier', 'Unknown')})\n"
                formatted += f"Title: {article['title']}\n"
                
                # Smart content selection based on tier and budget
                content = self._select_optimal_content(article)
                formatted += f"Content: {content}\n\n"
                article_num += 1
        
        # Process macro articles
        if macro_articles:
            formatted += "=== MACRO ARTICLES (Market/Economic) ===\n\n"
            for article in macro_articles:
                formatted += f"Article {article_num} [MACRO]:\n"
                formatted += f"Source: {article['source']} (Tier {article.get('source_tier', 'Unknown')})\n"
                formatted += f"Title: {article['title']}\n"
                
                # Smart content selection
                content = self._select_optimal_content(article)
                formatted += f"Content: {content}\n\n"
                article_num += 1
        
        return formatted
    
    def _select_optimal_content(self, article: Dict) -> str:
        """
        Select optimal content based on source tier and budget constraints
        
        Args:
            article: Article dictionary
            
        Returns:
            Optimized content string
        """
        source_tier = article.get('source_tier', 4)
        full_content = article.get('full_content', '')
        snippet = article.get('snippet', '')
        
        # Tier 1 sources: Use first 1,000 chars of full content (high value)
        if source_tier == 1 and full_content and len(full_content) > len(snippet):
            return full_content[:1000] + ("..." if len(full_content) > 1000 else "")
        
        # Tier 2 sources: Use first 500 chars of full content or snippet
        elif source_tier == 2 and full_content and len(full_content) > len(snippet):
            return full_content[:500] + ("..." if len(full_content) > 500 else "")
        
        # Tier 3+ or fallback: Use snippet only (cost-effective)
        else:
            return snippet
    
    def _create_batch_prompt(self, formatted_articles: str) -> List:
        """
        Create optimized batch prompt for single API call
        
        Args:
            formatted_articles: Pre-formatted article content
            
        Returns:
            List of message objects for LLM
        """
        from langchain_core.messages import SystemMessage, HumanMessage
        
        system_prompt = """Role: Senior Data Physics Analyst specializing in Batch Sentiment Analysis for NVIDIA Stock Prediction.

Objective: Analyze ALL provided articles as a unified "Informational Gravity System" and calculate combined market impact on NVIDIA.

METHODOLOGY:
1. COMPANY ARTICLES: Direct NVIDIA impact (earnings, products, leadership) = 1.0 weight
2. MACRO ARTICLES: Indirect market impact (Fed policy, tech sector, economy) = 0.4 weight
3. SOURCE WEIGHTING: Tier 1 (Bloomberg, Reuters) = 1.0 | Tier 2-3 = 0.7

OUTPUT REQUIREMENTS (Strict JSON Format):
{{
  "point_score": [Weighted average from -100 to +100],
  "probability_range": "[Min] to [Max]",
  "entropy": "[High/Medium/Low]",
  "company_impact": [Company articles influence -100 to +100],
  "macro_impact": [Macro articles influence -100 to +100],
  "reasoning": "[2 sentence summary of key factors]"
}}

Focus on: Earnings data, analyst ratings, Fed policy, tech sector trends, geopolitical risks."""
        
        return [
            SystemMessage(content=system_prompt), 
            HumanMessage(content=formatted_articles)
        ]
    
    def _parse_batch_response(self, response_text: str, company_articles: List[Dict], macro_articles: List[Dict]) -> Dict:
        """
        Parse JSON response from batch analysis
        
        Args:
            response_text: Raw GPT response
            company_articles: Original company articles
            macro_articles: Original macro articles
            
        Returns:
            Parsed results dictionary
        """
        import json
        import re
        
        try:
            # Clean and extract JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
                
                # Validate and normalize results
                point_score = float(result.get('point_score', 0))
                probability_range = result.get('probability_range', '0 to 0')
                entropy = result.get('entropy', 'Low')
                company_impact = float(result.get('company_impact', 0))
                macro_impact = float(result.get('macro_impact', 0))
                reasoning = result.get('reasoning', 'No reasoning provided')
                
                # Ensure score is within bounds
                point_score = max(-100, min(100, point_score))
                company_impact = max(-100, min(100, company_impact))
                macro_impact = max(-100, min(100, macro_impact))
                
                return {
                    "point_score": point_score,
                    "probability_range": probability_range,
                    "entropy": entropy,
                    "company_impact": company_impact,
                    "macro_impact": macro_impact,
                    "reasoning": reasoning,
                    "company_count": len(company_articles),
                    "macro_count": len(macro_articles),
                    "total_articles": len(company_articles) + len(macro_articles)
                }
            else:
                raise ValueError("No valid JSON found in response")
                
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Error parsing batch response: {str(e)}")
            logger.debug(f"Raw response: {response_text[:500]}...")
            
            # Fallback result
            return {
                "point_score": 0.0,
                "probability_range": "0 to 0",
                "entropy": "Low", 
                "company_impact": 0.0,
                "macro_impact": 0.0,
                "reasoning": f"Analysis failed: {str(e)}",
                "company_count": len(company_articles),
                "macro_count": len(macro_articles),
                "total_articles": len(company_articles) + len(macro_articles)
            }
    
    def _analyze_with_context(self, articles: List[Dict], article_type: str) -> Dict:
        """
        Analyze articles with specific context (company or macro)
        
        Args:
            articles: List of articles to analyze
            article_type: 'company' or 'macro'
        
        Returns:
            Sentiment analysis result
        """
        if not articles:
            return {
                "overall_score": 0.0,
                "confidence": "Low",
                "article_scores": [],
                "key_factors": f"No {article_type} articles"
            }
        
        try:
            # Use different prompt based on article type
            if article_type == "macro":
                prompt = ChatPromptTemplate.from_messages([
                    ("system", self._get_macro_system_prompt()),
                    ("user", "{articles}")
                ])
            else:
                prompt = self.sentiment_prompt
            
            # Format articles
            articles_text = self._format_articles_for_analysis(articles)
            
            # Create messages
            messages = prompt.format_messages(articles=articles_text)
            
            # Call GPT-4
            response = self.llm.invoke(messages)
            analysis_text = response.content
            
            # Debug: Log the actual response
            logger.debug(f"Full AI response for {article_type}: {analysis_text[:1000]}...")
            
            # Parse response - try JSON format first, fallback to text parsing
            result = self._parse_gravity_response(analysis_text, articles, article_type)
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing {article_type} sentiment: {str(e)}")
            return {
                "overall_score": 0.0,
                "confidence": "Low",
                "article_scores": [],
                "key_factors": f"Error: {str(e)}"
            }
    
    def _format_articles_for_analysis(self, articles: List[Dict]) -> str:
        """
        Format articles for GPT-4 analysis
        
        Args:
            articles: List of article dictionaries
        
        Returns:
            Formatted string
        """
        formatted = f"Analyze the following {len(articles)} NVIDIA news articles:\n\n"
        
        for i, article in enumerate(articles, 1):
            source_tier = article.get('source_tier', 0)
            tier_label = f"(Tier {source_tier})" if source_tier > 0 else ""
            
            formatted += f"Article {i} - {article['source']} {tier_label}:\n"
            formatted += f"Title: {article['title']}\n"
            formatted += f"Content: {article.get('snippet', 'No content available')}\n"
            formatted += f"URL: {article['url']}\n\n"
        
        return formatted
    
    def _parse_gravity_response(self, response_text: str, articles: List[Dict], article_type: str) -> Dict:
        """
        Parse GPT-4 response in new JSON gravity format
        
        Args:
            response_text: Raw GPT-4 response
            articles: Original articles for reference
            article_type: 'company' or 'macro'
        
        Returns:
            Structured sentiment results with gravity data
        """
        import json
        import re
        
        # Try to extract and parse JSON from response
        try:
            # Look for JSON block in the response - try multiple approaches
            json_str = None
            
            # Method 1: Look for complete JSON object
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            
            # Method 2: If no complete object, look for JSON between code blocks
            if not json_str:
                code_block_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if code_block_match:
                    json_str = code_block_match.group(1)
            
            # Method 3: Look for JSON between any code blocks
            if not json_str:
                any_code_block = re.search(r'```\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if any_code_block:
                    json_str = any_code_block.group(1)
            
            if json_str:
                # Clean the JSON string
                json_str = json_str.strip()
                logger.debug(f"Extracted JSON: {json_str[:100]}...")
                gravity_data = json.loads(json_str)
                
                # Extract data from JSON structure
                articles_analysis = gravity_data.get('articles_analysis', [])
                aggregated = gravity_data.get('aggregated_results', {})
                
                # Process individual articles
                article_scores = []
                for i, article_data in enumerate(articles_analysis):
                    if i < len(articles):
                        # Update article with gravity data
                        articles[i]['gravitational_mass'] = article_data.get('mass', 1.0)
                        articles[i]['field_vector'] = article_data.get('vector', 0.0)
                        
                        article_scores.append({
                            'article_no': article_data.get('article_no', i + 1),
                            'source': article_data.get('source', articles[i].get('source', 'Unknown')),
                            'mass': article_data.get('mass', 1.0),
                            'vector': article_data.get('vector', 0.0),
                            'reasoning': article_data.get('reasoning', 'No reasoning provided')
                        })
                
                # Return structured result
                return {
                    "overall_score": aggregated.get('point_score', 0.0),
                    "confidence": aggregated.get('entropy', 'Low').title(),
                    "article_scores": article_scores,
                    "key_factors": aggregated.get('final_summary', f"No {article_type} analysis"),
                    "probability_range": aggregated.get('probability_range', ''),
                    "entropy": aggregated.get('entropy', 'Low'),
                    "raw_analysis": response_text
                }
                
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"JSON parsing failed for {article_type} analysis: {str(e)}")
            # Fallback to legacy text parsing
            return self._parse_sentiment_response(response_text, articles)
        
        # Fallback if no JSON found
        logger.warning(f"No valid JSON found in {article_type} response, using text parsing")
        return self._parse_sentiment_response(response_text, articles)
    
    def _calculate_combined_range(self, company_result: Dict, macro_result: Dict) -> str:
        """Calculate combined probability range from company and macro results"""
        company_range = company_result.get('probability_range', '')
        macro_range = macro_result.get('probability_range', '')
        
        if not company_range and not macro_range:
            return ''
        elif not company_range:
            return macro_range
        elif not macro_range:
            return company_range
        else:
            # Average the ranges (simplified approach)
            try:
                from utils.database_manager import DatabaseManager
                company_width = DatabaseManager.calculate_range_width(company_range)
                macro_width = DatabaseManager.calculate_range_width(macro_range)
                avg_width = (company_width + macro_width) / 2
                center = 0  # Assume center around 0
                half_width = avg_width / 2
                return f"{center - half_width:.1f} to {center + half_width:.1f}"
            except:
                return company_range  # Fallback to company range
    
    def _calculate_combined_entropy(self, company_result: Dict, macro_result: Dict) -> str:
        """Calculate combined entropy from company and macro results"""
        company_entropy = company_result.get('entropy', 'Low')
        macro_entropy = macro_result.get('entropy', 'Low')
        
        # Simple entropy combination logic
        entropy_values = {'Low': 1, 'Medium': 2, 'High': 3}
        avg_entropy = (entropy_values.get(company_entropy, 1) + entropy_values.get(macro_entropy, 1)) / 2
        
        if avg_entropy >= 2.5:
            return 'High'
        elif avg_entropy >= 1.5:
            return 'Medium'
        else:
            return 'Low'
    
    def _save_article_gravity_data(self, articles: List[Dict]):
        """Save gravitational mass and field vectors for individual articles"""
        from utils.database_manager import DatabaseManager
        db = DatabaseManager()
        
        for article in articles:
            if 'gravitational_mass' in article and 'field_vector' in article and 'id' in article:
                db.update_article_gravity_data(
                    article_id=article['id'],
                    gravitational_mass=article['gravitational_mass'],
                    field_vector=article['field_vector']
                )
    
    def _parse_sentiment_response(self, response_text: str, articles: List[Dict]) -> Dict:
        """
        Parse GPT-4 sentiment analysis response
        
        Args:
            response_text: Raw GPT-4 response
            articles: Original articles for reference
        
        Returns:
            Structured sentiment results
        """
        # Extract overall sentiment score
        overall_score = self._extract_overall_score(response_text)
        
        # Extract confidence
        confidence = self._extract_confidence(response_text)
        
        # Extract key factors
        key_factors = self._extract_key_factors(response_text)
        
        # Extract individual article scores
        article_scores = self._extract_article_scores(response_text, len(articles))
        
        return {
            "overall_score": overall_score,
            "confidence": confidence,
            "article_scores": article_scores,
            "key_factors": key_factors,
            "raw_analysis": response_text
        }
    
    def _extract_overall_score(self, text: str) -> float:
        """Extract overall sentiment score from response"""
        import re
        
        # Look for patterns like "OVERALL SENTIMENT: 45" or "Overall: 45.5"
        patterns = [
            r'OVERALL SENTIMENT:\s*(-?\d+\.?\d*)',
            r'Overall:\s*(-?\d+\.?\d*)',
            r'overall score.*?(-?\d+\.?\d*)',
            r'weighted average.*?(-?\d+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                score = float(match.group(1))
                # Clamp to valid range
                score = max(SENTIMENT_SCALE[0], min(SENTIMENT_SCALE[1], score))
                logger.debug(f"Extracted overall score: {score}")
                return score
        
        logger.warning("Could not extract overall score, defaulting to 0")
        return 0.0
    
    def _extract_confidence(self, text: str) -> str:
        """Extract confidence level from response"""
        text_lower = text.lower()
        
        if 'confidence: high' in text_lower or 'high confidence' in text_lower:
            return "High"
        elif 'confidence: medium' in text_lower or 'medium confidence' in text_lower:
            return "Medium"
        elif 'confidence: low' in text_lower or 'low confidence' in text_lower:
            return "Low"
        
        return "Medium"  # Default
    
    def _extract_key_factors(self, text: str) -> str:
        """Extract key factors from response"""
        import re
        
        # Look for "KEY FACTORS:" section
        pattern = r'KEY FACTORS?:\s*(.+?)(?:\n\n|\Z)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            factors = match.group(1).strip()
            return factors
        
        # Fallback: Return first 200 chars as summary
        return text[:200] + "..."
    
    def _extract_article_scores(self, text: str, num_articles: int) -> List[Dict]:
        """Extract individual article scores from response"""
        import re
        
        article_scores = []
        
        # Look for patterns like "Sentiment score: 50" or "Score: 50"
        score_patterns = [
            r'Article \d+.*?[Ss]core:\s*(-?\d+\.?\d*)',
            r'[Ss]entiment.*?:\s*(-?\d+\.?\d*)',
        ]
        
        for i in range(1, num_articles + 1):
            # Try to find score for this article
            article_section = re.search(
                f'Article {i}.*?(?=Article {i+1}|OVERALL|$)',
                text,
                re.DOTALL | re.IGNORECASE
            )
            
            score = 0.0
            if article_section:
                section_text = article_section.group(0)
                for pattern in score_patterns:
                    match = re.search(pattern, section_text)
                    if match:
                        score = float(match.group(1))
                        break
            
            article_scores.append({
                "article_number": i,
                "score": score
            })
        
        return article_scores
    
    def analyze_single_article(self, article: Dict) -> float:
        """
        Analyze sentiment of a single article (quick analysis)
        
        Args:
            article: Article dictionary
        
        Returns:
            Sentiment score
        """
        result = self.analyze_articles([article])
        return result['overall_score']


# ============================================
# MODULE TEST
# ============================================
if __name__ == "__main__":
    """Test the sentiment agent"""
    from utils.logger import log_section_header
    
    logger = setup_logger("test_sentiment_agent")
    log_section_header(logger, "Sentiment Agent Test")
    
    # Create mock articles for testing
    mock_articles = [
        {
            "title": "NVIDIA Reports Record Q4 Earnings, Beats Expectations",
            "source": "Bloomberg",
            "source_tier": 1,
            "snippet": "NVIDIA Corporation reported quarterly earnings that exceeded analyst expectations, with revenue up 265% year-over-year driven by strong AI chip demand.",
            "url": "https://example.com/article1"
        },
        {
            "title": "Analysts Raise NVIDIA Price Target to $200",
            "source": "Reuters",
            "source_tier": 1,
            "snippet": "Major investment banks have raised their price targets for NVIDIA following strong data center growth and AI market expansion.",
            "url": "https://example.com/article2"
        },
        {
            "title": "NVIDIA Faces Increased Competition in AI Chip Market",
            "source": "CNBC",
            "source_tier": 1,
            "snippet": "AMD and Intel are ramping up their AI chip offerings, potentially challenging NVIDIA's dominance in the growing market.",
            "url": "https://example.com/article3"
        }
    ]
    
    # Check if OpenAI API key is set
    from config.settings import OPENAI_API_KEY
    
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set. Add it to .env file to test.")
        logger.info("\nShowing mock analysis structure:")
        print("\n" + "="*60)
        print("Mock Articles:")
        for i, article in enumerate(mock_articles, 1):
            print(f"\n{i}. {article['source']}: {article['title']}")
        print("\n" + "="*60)
        print("\nExpected output structure:")
        print("""
{
    "overall_score": 45.5,
    "confidence": "High",
    "article_scores": [
        {"article_number": 1, "score": 75},
        {"article_number": 2, "score": 60},
        {"article_number": 3, "score": -15}
    ],
    "key_factors": "Strong earnings beat expectations..."
}
        """)
    else:
        # Initialize agent
        agent = SentimentAgent()
        
        # Analyze mock articles
        logger.info("\nAnalyzing mock articles...")
        result = agent.analyze_articles(mock_articles)
        
        # Display results
        print("\n" + "="*60)
        print("SENTIMENT ANALYSIS RESULTS")
        print("="*60)
        print(f"\nOverall Score: {result['overall_score']:.2f}")
        print(f"Confidence: {result['confidence']}")
        print(f"\nKey Factors:\n{result['key_factors']}")
        
        if result.get('article_scores'):
            print(f"\nIndividual Article Scores:")
            for score_info in result['article_scores']:
                num = score_info['article_number']
                score = score_info['score']
                print(f"  Article {num}: {score:.1f}")
        
        print("\n" + "="*60)
        
        logger.info("\n✓ Sentiment agent test complete!")
