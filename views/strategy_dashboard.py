#!/usr/bin/env python3
"""
StrategyAgent-Enhanced Dashboard View
Professional presentation of dynamic weight analysis and strategic insights
"""

import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

from data.database_manager import DatabaseManager
from agents.orchestrator_agent import OrchestratorAgent
from data.market_data_fetcher import MarketDataFetcher
from config.settings import NVIDIA_SYMBOL


class StrategyDashboard:
    """Professional dashboard for StrategyAgent insights"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.orchestrator = OrchestratorAgent()
        self.market_fetcher = MarketDataFetcher()
    
    def display_current_strategy_analysis(self, target_date: str = None) -> Dict[str, Any]:
        """Display detailed StrategyAgent analysis for a specific date"""
        
        if not target_date:
            target_date = datetime.now().strftime('%Y-%m-%d')
        
        print("\n" + "=" * 80)
        print(f"STRATEGY AGENT ANALYSIS DASHBOARD - {target_date}")
        print("=" * 80)
        
        # Get current data
        daily_data = self.db.get_daily_data(target_date)
        if not daily_data:
            print(f"❌ No market data found for {target_date}")
            return {}
        
        current_price = float(daily_data.get('close_price', 0))
        sentiment_score = float(daily_data.get('sentiment_score', 0))
        
        print(f"📊 MARKET CONTEXT:")
        print(f"   Date: {target_date}")
        print(f"   {NVIDIA_SYMBOL} Close: ${current_price:.2f}")
        print(f"   Raw Sentiment: {sentiment_score:+.2f}")
        
        # Get articles for the day
        articles = self.db.get_articles_for_date(target_date)
        company_articles = [a for a in articles if a.get('article_type') == 'company']
        macro_articles = [a for a in articles if a.get('article_type') == 'macro']
        
        print(f"\n📰 INFORMATION LANDSCAPE:")
        print(f"   Total Articles: {len(articles)}")
        print(f"   Company-Specific: {len(company_articles)}")
        print(f"   Macro-Economic: {len(macro_articles)}")
        
        # Create news summary for StrategyAgent
        news_summary = {
            'final_sentiment': sentiment_score,
            'company_count': len(company_articles),
            'macro_count': len(macro_articles),
            'company_sentiment': sentiment_score * 0.6 if company_articles else 0.0,
            'macro_sentiment': sentiment_score * 0.4 if macro_articles else 0.0
        }
        
        # Get StrategyAgent's dynamic analysis
        strategy_analysis = self.orchestrator.calculate_hybrid_signal(
            target_date, sentiment_score, news_summary
        )
        
        self._display_strategy_insights(strategy_analysis, news_summary)
        
        # Get technical context
        technical_data = self.market_fetcher.fetch_technical_data(target_date)
        if technical_data:
            self._display_technical_context(technical_data)
        
        # Display final recommendation
        self._display_trading_recommendation(strategy_analysis)
        
        return strategy_analysis
    
    def _display_strategy_insights(self, strategy_analysis: Dict, news_summary: Dict):
        """Display StrategyAgent's strategic reasoning"""
        
        print(f"\n🧠 STRATEGY AGENT INSIGHTS:")
        print("-" * 60)
        
        strategy_weights = strategy_analysis.get('strategy_weights', {})
        regime = strategy_weights.get('regime_analysis', 'UNKNOWN')
        sentiment_weight = strategy_weights.get('sentiment', 0.6)
        technical_weight = strategy_weights.get('technical', 0.4)
        
        print(f"📊 MARKET REGIME IDENTIFICATION:")
        print(f"   Current Regime: {regime}")
        print(f"   Dynamic Weights: Sentiment {sentiment_weight:.0%} | Technical {technical_weight:.0%}")
        
        if strategy_weights.get('strategic_reasoning'):
            reasoning = strategy_weights['strategic_reasoning']
            print(f"\n🎯 STRATEGIC REASONING:")
            # Split long reasoning into readable chunks
            words = reasoning.split()
            lines = []
            current_line = []
            for word in words:
                current_line.append(word)
                if len(' '.join(current_line)) > 65:
                    lines.append(' '.join(current_line[:-1]))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))
            
            for line in lines:
                print(f"   {line}")
        
        # Display boundary rule analysis
        print(f"\n🛡️ BOUNDARY RULE ANALYSIS:")
        applied_rules = strategy_weights.get('boundary_rules_applied', [])
        if applied_rules:
            for rule in applied_rules:
                print(f"   ✅ {rule}")
        else:
            print(f"   ⚪ No boundary rules triggered")
        
        # Information density analysis
        total_articles = news_summary.get('company_count', 0) + news_summary.get('macro_count', 0)
        print(f"\n📊 INFORMATION DENSITY:")
        print(f"   Article Volume: {total_articles} ({'High' if total_articles >= 5 else 'Medium' if total_articles >= 2 else 'Low'})")
        print(f"   Company Focus: {news_summary.get('company_count', 0)} articles")
        print(f"   Macro Focus: {news_summary.get('macro_count', 0)} articles")
        
        sentiment_strength = abs(news_summary.get('final_sentiment', 0))
        if sentiment_strength > 8:
            sentiment_intensity = "EXTREME"
        elif sentiment_strength > 5:
            sentiment_intensity = "HIGH"
        elif sentiment_strength > 2:
            sentiment_intensity = "MODERATE"
        else:
            sentiment_intensity = "LOW"
        
        print(f"   Sentiment Intensity: {sentiment_intensity} (|{sentiment_strength:.1f}|)")
    
    def _display_technical_context(self, technical_data: Dict):
        """Display technical analysis context"""
        
        print(f"\n⚙️ TECHNICAL FRICTION ANALYSIS:")
        print("-" * 60)
        
        technical_score = technical_data.get('technical_score', 0)
        rsi = technical_data.get('rsi', 50)
        momentum_3d = technical_data.get('momentum_3d', 0)
        ma_position = technical_data.get('ma_position', 'UNKNOWN')
        
        print(f"📈 TECHNICAL INDICATORS:")
        print(f"   Technical Score: {technical_score:+.2f}")
        print(f"   RSI(14): {rsi:.1f} - {technical_data.get('rsi_pressure', 'NEUTRAL')}")
        print(f"   3-Day Momentum: {momentum_3d:+.1f}% - {technical_data.get('momentum_direction', 'FLAT')}")
        print(f"   Moving Average Position: {ma_position}")
        
        # Technical regime analysis
        if rsi > 70:
            rsi_regime = "OVERBOUGHT"
        elif rsi < 30:
            rsi_regime = "OVERSOLD"
        else:
            rsi_regime = "NEUTRAL"
        
        if abs(momentum_3d) > 3:
            momentum_regime = "TRENDING"
        elif abs(momentum_3d) > 1:
            momentum_regime = "MOVING"
        else:
            momentum_regime = "CONSOLIDATING"
        
        print(f"\n🔍 TECHNICAL REGIME:")
        print(f"   RSI Regime: {rsi_regime}")
        print(f"   Momentum Regime: {momentum_regime}")
        print(f"   Overall Technical Bias: {'BULLISH' if technical_score > 1 else 'BEARISH' if technical_score < -1 else 'NEUTRAL'}")
    
    def _display_trading_recommendation(self, strategy_analysis: Dict):
        """Display final trading recommendation with confidence metrics"""
        
        print(f"\n🎯 TRADING RECOMMENDATION:")
        print("=" * 60)
        
        final_gravity = strategy_analysis.get('final_gravity', 0)
        strategy_weights = strategy_analysis.get('strategy_weights', {})
        
        # Convert to signal
        if final_gravity > 5:
            signal = "STRONG BUY"
            confidence = "HIGH"
            direction = "BULLISH"
        elif final_gravity > 2:
            signal = "BUY"
            confidence = "MEDIUM"
            direction = "BULLISH"
        elif final_gravity > 0:
            signal = "WEAK BUY"
            confidence = "LOW"
            direction = "SLIGHTLY BULLISH"
        elif final_gravity < -5:
            signal = "STRONG SELL"
            confidence = "HIGH"
            direction = "BEARISH"
        elif final_gravity < -2:
            signal = "SELL"
            confidence = "MEDIUM"
            direction = "BEARISH"
        elif final_gravity < 0:
            signal = "WEAK SELL"
            confidence = "LOW"
            direction = "SLIGHTLY BEARISH"
        else:
            signal = "HOLD"
            confidence = "NEUTRAL"
            direction = "SIDEWAYS"
        
        print(f"📊 FINAL SIGNAL: {signal}")
        print(f"🎯 Direction: {direction}")
        print(f"💪 Confidence: {confidence}")
        print(f"📏 Final Gravity: {final_gravity:+.2f}")
        
        # Risk assessment
        sentiment_weight = strategy_weights.get('sentiment', 0.6)
        if sentiment_weight > 0.7:
            risk_profile = "NEWS-DRIVEN (High Info Dependency)"
        elif sentiment_weight < 0.4:
            risk_profile = "TECHNICAL-DRIVEN (Market Structure Focus)"
        else:
            risk_profile = "BALANCED (Mixed Signals)"
        
        print(f"⚠️  Risk Profile: {risk_profile}")
        
        # Strategic notes
        print(f"\n📝 STRATEGIC NOTES:")
        if abs(final_gravity) < 1:
            print(f"   • Weak signal - Consider waiting for clearer confirmation")
        if sentiment_weight != 0.6:  # Default weight
            print(f"   • Dynamic weighting active - Strategy adapted to market conditions")
        if 'HIGH_MASS' in str(strategy_weights.get('boundary_rules_applied', [])):
            print(f"   • High-mass sentiment detected - Increased information weight")
        if 'NOISE_RULE' in str(strategy_weights.get('boundary_rules_applied', [])):
            print(f"   • Market noise detected - Reduced sentiment influence")
    
    def display_week_overview(self, weeks_back: int = 1):
        """Display strategic overview for recent trading week"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=weeks_back * 7)
        
        print("\n" + "=" * 80)
        print(f"STRATEGY AGENT WEEKLY OVERVIEW")
        print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print("=" * 80)
        
        # Get all trading days in range
        trading_days = []
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:  # Monday to Friday
                date_str = current.strftime('%Y-%m-%d')
                daily_data = self.db.get_daily_data(date_str)
                if daily_data:
                    trading_days.append(date_str)
            current += timedelta(days=1)
        
        if not trading_days:
            print("❌ No trading data found for the specified period")
            return
        
        print(f"📊 TRADING DAYS ANALYZED: {len(trading_days)}")
        print(f"{'Date':<12} {'Price':<8} {'Sentiment':<10} {'S/T Weights':<12} {'Signal':<12}")
        print("-" * 65)
        
        total_sentiment_weight = 0
        total_technical_weight = 0
        regime_distribution = {}
        
        for date in trading_days:
            daily_data = self.db.get_daily_data(date)
            price = float(daily_data.get('close_price', 0))
            sentiment = float(daily_data.get('sentiment_score', 0))
            
            # Quick strategy analysis
            news_summary = {'final_sentiment': sentiment, 'company_count': 2, 'macro_count': 1}
            strategy_result = self.orchestrator.calculate_hybrid_signal(date, sentiment, news_summary)
            
            weights = strategy_result.get('strategy_weights', {})
            s_weight = weights.get('sentiment', 0.6)
            t_weight = weights.get('technical', 0.4)
            regime = weights.get('regime_analysis', 'UNKNOWN')
            
            final_gravity = strategy_result.get('final_gravity', sentiment)
            
            if final_gravity > 2:
                signal = "BUY"
            elif final_gravity < -2:
                signal = "SELL"
            else:
                signal = "HOLD"
            
            print(f"{date:<12} ${price:<7.2f} {sentiment:+8.2f} {s_weight:.1f}/{t_weight:.1f}{'':>7} {signal:<12}")
            
            total_sentiment_weight += s_weight
            total_technical_weight += t_weight
            regime_distribution[regime] = regime_distribution.get(regime, 0) + 1
        
        avg_s_weight = total_sentiment_weight / len(trading_days)
        avg_t_weight = total_technical_weight / len(trading_days)
        
        print("-" * 65)
        print(f"📊 WEEKLY STRATEGY SUMMARY:")
        print(f"   Average Weights: Sentiment {avg_s_weight:.1%} | Technical {avg_t_weight:.1%}")
        print(f"   Regime Distribution: {dict(regime_distribution)}")
        
        if len(set(regime_distribution.keys())) > 1:
            print(f"   ✅ Dynamic adaptation active across multiple market regimes")
        else:
            print(f"   ⚪ Consistent regime identification throughout period")


def main():
    """Interactive dashboard menu"""
    dashboard = StrategyDashboard()
    
    if len(sys.argv) > 1:
        # Command line date argument
        target_date = sys.argv[1]
        dashboard.display_current_strategy_analysis(target_date)
    else:
        # Interactive mode
        while True:
            print("\n🎯 STRATEGY AGENT DASHBOARD")
            print("1. Today's Strategy Analysis")
            print("2. Specific Date Analysis")
            print("3. Weekly Overview")
            print("4. Exit")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                dashboard.display_current_strategy_analysis()
            elif choice == "2":
                date_input = input("Enter date (YYYY-MM-DD): ").strip()
                try:
                    datetime.strptime(date_input, '%Y-%m-%d')
                    dashboard.display_current_strategy_analysis(date_input)
                except ValueError:
                    print("❌ Invalid date format. Use YYYY-MM-DD")
            elif choice == "3":
                weeks = input("How many weeks back? (default 1): ").strip()
                weeks = int(weeks) if weeks.isdigit() else 1
                dashboard.display_week_overview(weeks)
            elif choice == "4":
                print("👋 Exiting Strategy Dashboard")
                break
            else:
                print("❌ Invalid option. Please select 1-4.")


if __name__ == "__main__":
    main()