"""
News Agent
Searches for NVIDIA-related news using Serper API and filters for relevance
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from agents.base_agent import BaseAgent
from config.settings import SERPER_API_KEY, MAX_NEWS_ARTICLES, STOCK_NAME
from config.trusted_sources import (
    is_trusted_source,
    is_trusted_company_source,
    is_trusted_macro_source,
    is_excluded_source, 
    get_source_tier,
    get_company_source_tier,
    get_macro_source_tier,
    NVIDIA_KEYWORDS
)
from utils.logger import setup_logger

logger = setup_logger(__name__)


class NewsAgent(BaseAgent):
    """AI Agent for searching and filtering NVIDIA news"""
    
    def __init__(self):
        """Initialize News Agent with Serper API"""
        super().__init__("NewsAgent", temperature=0.3)  # Lower temp for focused search
        
        if not SERPER_API_KEY:
            raise ValueError("SERPER_API_KEY not set in environment")
        
        self.api_key = SERPER_API_KEY
        self.base_url = "https://google.serper.dev/news"
        logger.info("NewsAgent ready with Serper API")
    
    def search_news(self, date: Optional[str] = None, max_results: int = MAX_NEWS_ARTICLES) -> List[Dict]:
        """
        Search for NVIDIA news articles for a specific date
        
        Args:
            date: Date in YYYY-MM-DD format (default: today)
            max_results: Maximum number of articles to return
        
        Returns:
            List of filtered and validated news articles with article_type='company'
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Searching for NVIDIA news on {date}")
        
        try:
            # Build search query
            query = self._build_search_query(date)
            
            # Call Serper API
            raw_articles = self._call_serper_api(query)
            
            if not raw_articles:
                logger.warning(f"No articles found for {date}")
                return []
            
            logger.info(f"Found {len(raw_articles)} raw articles from Serper")
            
            # Filter and validate articles
            filtered_articles = self._filter_articles(raw_articles, date)
            
            # Sort by source tier and limit results
            filtered_articles = self._rank_and_limit(filtered_articles, max_results)
            
            # Mark as company-specific articles
            for article in filtered_articles:
                article['article_type'] = 'company'
            
            logger.info(f"Filtered to {len(filtered_articles)} relevant articles")
            return filtered_articles
            
        except Exception as e:
            logger.error(f"Error searching news: {str(e)}")
            return []
    
    def search_macro_news(self, date: Optional[str] = None, max_results: int = MAX_NEWS_ARTICLES) -> List[Dict]:
        """
        Search for macro/market news articles
        
        Args:
            date: Date in YYYY-MM-DD format (default: today)
            max_results: Maximum number of articles to return
        
        Returns:
            List of filtered and validated articles with article_type='macro'
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Searching for macro/market news on {date}")
        
        try:
            # Build macro search query
            query = self._build_macro_search_query(date)
            
            # Call Serper API
            raw_articles = self._call_serper_api(query)
            
            if not raw_articles:
                logger.warning(f"No macro articles found for {date}")
                return []
            
            logger.info(f"Found {len(raw_articles)} raw macro articles from Serper")
            
            # Filter macro articles (different criteria than company news)
            filtered_articles = self._filter_macro_articles(raw_articles, date)
            
            # Sort by source tier and limit results
            filtered_articles = self._rank_and_limit(filtered_articles, max_results)
            
            # Mark as macro articles
            for article in filtered_articles:
                article['article_type'] = 'macro'
            
            logger.info(f"Filtered to {len(filtered_articles)} relevant macro articles")
            return filtered_articles
            
        except Exception as e:
            logger.error(f"Error searching macro news: {str(e)}")
            return []
    
    def _build_search_query(self, date: str) -> str:
        """
        Build optimized search query for NVIDIA news
        
        Args:
            date: Target date
        
        Returns:
            Search query string
        """
        # Focus on NVIDIA stock and company news
        query = f'NVIDIA OR NVDA OR "Jensen Huang" stock news {date}'
        
        logger.debug(f"Search query: {query}")
        return query
    
    def _build_macro_search_query(self, date: str) -> str:
        """
        Build optimized search query for macro/market news
        
        Args:
            date: Target date
        
        Returns:
            Search query string
        """
        # Target multiple trusted sources with varied market terms
        # Using two separate queries to get more results
        query = f'(site:bloomberg.com OR site:reuters.com OR site:cnbc.com OR site:wsj.com OR site:marketwatch.com OR site:barrons.com) stock market NASDAQ {date}'
        
        logger.debug(f"Macro search query: {query}")
        return query
    
    def _call_serper_api(self, query: str) -> List[Dict]:
        """
        Call Serper API to search for news
        
        Args:
            query: Search query string
        
        Returns:
            List of raw articles from API
        """
        try:
            headers = {
                'X-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            }
            
            payload = {
                'q': query,
                'num': 20,  # Get more for filtering
                'type': 'news'
            }
            
            logger.debug(f"Calling Serper API with query: {query}")
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract news articles
            articles = data.get('news', [])
            logger.debug(f"Serper returned {len(articles)} articles")
            
            return articles
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Serper API request failed: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error calling Serper API: {str(e)}")
            return []
    
    def _filter_articles(self, articles: List[Dict], target_date: str) -> List[Dict]:
        """
        Filter articles for relevance and trusted sources
        
        Args:
            articles: Raw articles from API
            target_date: Target date for filtering
        
        Returns:
            Filtered list of articles
        """
        filtered = []
        
        for article in articles:
            # Extract article info
            title = article.get('title', '')
            source = article.get('source', '')
            link = article.get('link', '')
            snippet = article.get('snippet', '')
            
            # Skip if missing critical info
            if not title or not source or not link:
                logger.debug(f"Skipping article with missing info")
                continue
            
            # Filter by source trustworthiness - STRICT: Only trusted sources
            if is_excluded_source(source):
                logger.debug(f"Excluded source: {source}")
                continue
            
            # STRICT: Only accept trusted COMPANY sources (tech + financial)
            if not is_trusted_company_source(source):
                logger.debug(f"Rejecting untrusted company source: {source}")
                continue
            
            # Filter by source tier - accept tier 1, 2, or 3 only
            source_tier = get_company_source_tier(source)
            if source_tier > 3:
                logger.debug(f"Rejecting low-tier company source: {source} (tier {source_tier})")
                continue
            
            # Check if NVIDIA-related
            if not self._is_nvidia_relevant(title, snippet):
                logger.debug(f"Not NVIDIA-relevant: {title[:50]}")
                continue
            
            # Build standardized article format
            filtered_article = {
                'title': title,
                'source': source,
                'url': link,
                'snippet': snippet,
                'date': target_date,
                'source_tier': get_company_source_tier(source),
                'is_trusted': is_trusted_company_source(source)
            }
            
            filtered.append(filtered_article)
            logger.debug(f"Added company article: {title[:50]}... from {source} (tier {get_company_source_tier(source)})")
        
        return filtered
    
    def _filter_macro_articles(self, articles: List[Dict], target_date: str) -> List[Dict]:
        """
        Filter macro/market articles for relevance and trusted sources
        
        Args:
            articles: Raw articles from API
            target_date: Target date for filtering
        
        Returns:
            Filtered list of macro articles
        """
        filtered = []
        
        for article in articles:
            # Extract article info
            title = article.get('title', '')
            source = article.get('source', '')
            link = article.get('link', '')
            snippet = article.get('snippet', '')
            
            # Skip if missing critical info
            if not title or not source or not link:
                logger.debug(f"Skipping macro article with missing info")
                continue
            
            # STRICT: Only accept trusted MACRO sources (financial focus)
            if not is_trusted_macro_source(source):
                logger.debug(f"Rejecting untrusted macro source: {source}")
                continue
            
            # Filter by source tier - accept tier 1, 2, or 3 (still good quality)
            source_tier = get_macro_source_tier(source)
            if source_tier > 3:
                logger.debug(f"Rejecting low-tier macro source: {source} (tier {source_tier})")
                continue
            
            # Check if macro/market relevant (broader than NVIDIA-specific)
            if not self._is_macro_relevant(title, snippet):
                logger.debug(f"Not macro-relevant: {title[:50]}")
                continue
            
            # Build standardized article format
            filtered_article = {
                'title': title,
                'source': source,
                'url': link,
                'snippet': snippet,
                'date': target_date,
                'source_tier': get_macro_source_tier(source),
                'is_trusted': is_trusted_macro_source(source)
            }
            
            filtered.append(filtered_article)
            logger.debug(f"Added macro article: {title[:50]}... from {source} (tier {get_macro_source_tier(source)})")
        
        return filtered
    
    def _is_nvidia_relevant(self, title: str, snippet: str) -> bool:
        """
        Check if article is NVIDIA-relevant
        
        Args:
            title: Article title
            snippet: Article snippet
        
        Returns:
            True if relevant, False otherwise
        """
        text = f"{title} {snippet}".lower()
        
        # Check for NVIDIA keywords
        for keyword in NVIDIA_KEYWORDS:
            if keyword.lower() in text:
                return True
        
        return False
    
    def _is_macro_relevant(self, title: str, snippet: str) -> bool:
        """
        Check if article is macro/market relevant
        
        Args:
            title: Article title
            snippet: Article snippet
        
        Returns:
            True if relevant, False otherwise
        """
        text = f"{title} {snippet}".lower()
        
        # Check for macro/market keywords
        macro_keywords = [
            'stock market', 'nasdaq', 'dow jones', 's&p 500', 'wall street',
            'federal reserve', 'fed', 'interest rate', 'inflation', 'cpi',
            'gdp', 'economy', 'recession', 'unemployment',
            'china', 'trade war', 'tariff', 'geopolitical', 'war',
            'tech sector', 'semiconductor', 'ai sector', 'tech stocks'
        ]
        
        for keyword in macro_keywords:
            if keyword.lower() in text:
                return True
        
        return False
    
    def _rank_and_limit(self, articles: List[Dict], max_results: int) -> List[Dict]:
        """
        Rank articles by source tier and limit to max_results
        
        Args:
            articles: Filtered articles
            max_results: Maximum number to return
        
        Returns:
            Top ranked articles
        """
        # Sort by: is_trusted (desc), source_tier (asc), then keep original order
        sorted_articles = sorted(
            articles,
            key=lambda x: (not x['is_trusted'], x['source_tier'])
        )
        
        # Limit to max_results
        limited = sorted_articles[:max_results]
        
        # Log the selection
        for i, article in enumerate(limited, 1):
            tier = article['source_tier']
            trust = "✓" if article['is_trusted'] else "✗"
            logger.info(f"  {i}. [{trust}] Tier {tier} - {article['source']}: {article['title'][:60]}...")
        
        return limited
    
    def format_articles_for_sentiment(self, articles: List[Dict]) -> str:
        """
        Format articles for sentiment analysis
        
        Args:
            articles: List of articles
        
        Returns:
            Formatted string for GPT analysis
        """
        if not articles:
            return "No articles found."
        
        formatted = f"NVIDIA News Articles ({len(articles)} articles):\n\n"
        
        for i, article in enumerate(articles, 1):
            formatted += f"Article {i}:\n"
            formatted += f"Source: {article['source']}\n"
            formatted += f"Title: {article['title']}\n"
            formatted += f"Content: {article['snippet']}\n"
            formatted += f"URL: {article['url']}\n\n"
        
        return formatted


# ============================================
# MODULE TEST
# ============================================
if __name__ == "__main__":
    """Test the news agent"""
    from utils.logger import log_section_header
    
    logger = setup_logger("test_news_agent")
    log_section_header(logger, "News Agent Test")
    
    # Check if API key is set
    if not SERPER_API_KEY:
        logger.error("SERPER_API_KEY not set. Add it to .env file to test.")
        logger.info("Skipping test - API key required")
    else:
        # Initialize agent
        agent = NewsAgent()
        
        # Test: Search for today's news
        logger.info("Test: Searching for NVIDIA news today...")
        articles = agent.search_news(max_results=3)
        
        if articles:
            logger.info(f"✓ Found {len(articles)} articles")
            
            # Show formatted output
            formatted = agent.format_articles_for_sentiment(articles)
            print("\n" + "="*60)
            print(formatted)
            print("="*60)
        else:
            logger.warning("No articles found")
        
        logger.info("\n✓ News agent test complete!")
