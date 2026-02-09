"""
Strategy Agent
Determines dynamic weights for Hybrid Formula based on market conditions
"""

import json
from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from utils.logger import setup_logger

logger = setup_logger(__name__)


class StrategyAgent(BaseAgent):
    """Agent that determines daily weights for sentiment-technical fusion"""
    
    def __init__(self):
        """Initialize the Strategy Agent"""
        super().__init__("StrategyAgent", temperature=0.3)
        logger.info("StrategyAgent initialized with rule-based weight determination")
    
    def determine_daily_strategy(self, news_summary: Dict[str, Any], technical_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine dynamic weights based on market conditions and boundary rules
        
        Args:
            news_summary: Summary of news analysis including sentiment and article types
            technical_data: Technical indicators including RSI, momentum, etc.
        
        Returns:
            Dict containing regime analysis, weights, boundary check, and reasoning
        """
        try:
            # Extract key data points
            sentiment_score = news_summary.get('final_sentiment', 0)
            company_articles = news_summary.get('company_count', 0)
            macro_articles = news_summary.get('macro_count', 0)
            total_articles = company_articles + macro_articles
            
            rsi = technical_data.get('rsi', 50)
            momentum_3d = technical_data.get('momentum_3d', 0)
            tech_score = technical_data.get('tech_score', 0)
            
            # Apply LLM-based analysis with structured prompt
            analysis_prompt = self._build_strategy_prompt(
                sentiment_score, company_articles, macro_articles, total_articles,
                rsi, momentum_3d, tech_score
            )
            
            response = self.llm.invoke(analysis_prompt)
            strategy_result = self._parse_llm_response(response.content)
            
            # Validate and enforce boundary rules
            strategy_result = self._enforce_boundaries(strategy_result)
            
            logger.info(f"Strategy determined: Sentiment={strategy_result['applied_weights']['sentiment']:.2f}, Technical={strategy_result['applied_weights']['technical']:.2f}")
            
            return strategy_result
            
        except Exception as e:
            logger.error(f"Strategy determination failed: {e}")
            # Fallback to balanced weights if strategy fails
            return self._create_fallback_strategy()
    
    def _build_strategy_prompt(self, sentiment_score: float, company_articles: int, 
                              macro_articles: int, total_articles: int,
                              rsi: float, momentum_3d: float, tech_score: float) -> str:
        """
        Build structured prompt for weight determination
        """
        return f"""
You are a Strategic Weight Allocation Agent. Analyze the market data and determine optimal weights for sentiment vs technical analysis within STRICT BOUNDARIES.

MARKET DATA:
- Sentiment Score: {sentiment_score:.2f}
- Company Articles: {company_articles}
- Macro Articles: {macro_articles}
- Total Articles: {total_articles}
- RSI: {rsi:.1f}
- 3D Momentum: {momentum_3d:.2f}%
- Technical Score: {tech_score:.2f}

BOUNDARY RULES (MUST FOLLOW):
1. sentiment_weight MUST be between 0.2 and 0.8 (never 100% news or 100% technical)
2. sentiment_weight + technical_weight MUST equal 1.0
3. Safety Margin: Always maintain at least 20% allocation to each side

FOUNDATION RULES:
1. High-Mass Rule: Strong company-specific news (earnings, guidance) → sentiment_weight 0.7-0.8
2. Technical Friction Rule: Extreme RSI (>75 or <25) → technical_weight ≥ 0.6
3. Noise Rule: Low article count (<4) or weak sentiment → sentiment_weight 0.2-0.4

ANALYZE and determine weights based on these rules.

Respond ONLY in this JSON format:
{{
  "regime_analysis": "Brief description of market conditions",
  "applied_weights": {{
      "sentiment": 0.XX,
      "technical": 0.XX
  }},
  "boundary_check": "Confirmation of rule compliance",
  "strategic_reasoning": "Why these specific weights were chosen"
}}
"""
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response and extract strategy data
        """
        try:
            # Clean response and extract JSON
            cleaned = response.strip()
            if '```json' in cleaned:
                start = cleaned.find('{', cleaned.find('```json'))
                end = cleaned.rfind('}') + 1
                json_str = cleaned[start:end]
            elif '{' in cleaned:
                start = cleaned.find('{')
                end = cleaned.rfind('}') + 1
                json_str = cleaned[start:end]
            else:
                raise ValueError("No JSON found in response")
            
            result = json.loads(json_str)
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise
    
    def _enforce_boundaries(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enforce hard boundary rules on weight allocation
        """
        sentiment_weight = strategy['applied_weights']['sentiment']
        technical_weight = strategy['applied_weights']['technical']
        
        # Enforce weight limits
        sentiment_weight = max(0.2, min(0.8, sentiment_weight))
        technical_weight = 1.0 - sentiment_weight
        
        # Update strategy with enforced weights
        strategy['applied_weights']['sentiment'] = sentiment_weight
        strategy['applied_weights']['technical'] = technical_weight
        
        # Add boundary enforcement note
        if abs(sentiment_weight + technical_weight - 1.0) > 0.01:
            strategy['boundary_check'] += " [ENFORCED: Sum normalized to 1.0]"
        
        return strategy
    
    def _create_fallback_strategy(self) -> Dict[str, Any]:
        """
        Create fallback strategy if LLM fails
        """
        return {
            "regime_analysis": "Fallback mode - balanced allocation",
            "applied_weights": {
                "sentiment": 0.5,
                "technical": 0.5
            },
            "boundary_check": "Fallback weights within boundaries (0.2-0.8)",
            "strategic_reasoning": "LLM analysis failed, using balanced 50/50 allocation"
        }
