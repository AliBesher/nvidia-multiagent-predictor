"""
Sequential Day-by-Day Hybrid Analysis - Production Run Simulation
Treats each trading day as a standalone production run with full pipeline execution
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator_agent import OrchestratorAgent
from agents.sentiment_agent import SentimentAgent
from data.database_manager import DatabaseManager
from data.market_data_fetcher import MarketDataFetcher
from utils.logger import setup_logger
import time
from datetime import datetime, timedelta
from typing import List, Dict

logger = setup_logger(__name__)

# Complete 11-day sequence (Jan 16 to Feb 6)
SEQUENTIAL_DATES = [
    "2026-01-16", "2026-01-17", "2026-01-21", "2026-01-22", "2026-01-23",
    "2026-01-26", "2026-01-27", "2026-01-28", "2026-01-29", "2026-01-30", 
    "2026-02-02", "2026-02-05", "2026-02-06"
]

def get_next_trading_day(current_date: str, all_dates: List[str]) -> str:
    """Get the next trading day for gap comparison"""
    try:
        current_index = all_dates.index(current_date)
        if current_index < len(all_dates) - 1:
            return all_dates[current_index + 1]
        return None
    except ValueError:
        return None

def calculate_opening_gap(previous_close: float, next_open: float) -> Dict:
    """Calculate opening gap percentage and direction"""
    if not previous_close or not next_open:
        return {"gap_percent": 0.0, "gap_direction": "UNKNOWN", "gap_magnitude": "NONE"}
    
    gap_percent = ((next_open - previous_close) / previous_close) * 100
    gap_direction = "UP" if gap_percent > 0 else "DOWN" if gap_percent < 0 else "FLAT"
    
    # Classify gap magnitude
    abs_gap = abs(gap_percent)
    if abs_gap >= 5.0:
        gap_magnitude = "MAJOR"
    elif abs_gap >= 2.0:
        gap_magnitude = "SIGNIFICANT"  
    elif abs_gap >= 0.5:
        gap_magnitude = "MINOR"
    else:
        gap_magnitude = "NEGLIGIBLE"
    
    return {
        "gap_percent": gap_percent,
        "gap_direction": gap_direction, 
        "gap_magnitude": gap_magnitude
    }

def grade_prediction_accuracy(prediction_direction: str, actual_direction: str, 
                            prediction_magnitude: float, actual_magnitude: float) -> Dict:
    """Grade prediction accuracy on A-F scale"""
    
    # Direction accuracy (70% weight)
    direction_correct = prediction_direction == actual_direction
    direction_score = 1.0 if direction_correct else 0.0
    
    # Magnitude accuracy (30% weight) 
    if actual_magnitude == 0:
        magnitude_score = 1.0 if abs(prediction_magnitude) < 2 else 0.5
    else:
        magnitude_error = abs(prediction_magnitude - actual_magnitude) / max(abs(actual_magnitude), 1)
        magnitude_score = max(0, 1.0 - magnitude_error)
    
    # Combined score
    total_score = (direction_score * 0.7) + (magnitude_score * 0.3)
    
    # Convert to letter grade
    if total_score >= 0.9:
        grade = "A"
        description = "Excellent prediction"
    elif total_score >= 0.8:
        grade = "B" 
        description = "Good prediction"
    elif total_score >= 0.7:
        grade = "C"
        description = "Satisfactory prediction"
    elif total_score >= 0.6:
        grade = "D"
        description = "Poor prediction"
    else:
        grade = "F"
        description = "Failed prediction"
    
    return {
        "grade": grade,
        "score": total_score,
        "description": description,
        "direction_correct": direction_correct,
        "direction_score": direction_score,
        "magnitude_score": magnitude_score
    }

def get_prediction_signal(final_gravity: float) -> Dict:
    """Convert final gravity to trading signal"""
    if final_gravity > 5:
        return {"signal": "STRONG BUY", "direction": "UP", "confidence": "High"}
    elif final_gravity > 2:
        return {"signal": "BUY", "direction": "UP", "confidence": "Medium"}
    elif final_gravity > 0:
        return {"signal": "WEAK BUY", "direction": "UP", "confidence": "Low"}
    elif final_gravity < -5:
        return {"signal": "STRONG SELL", "direction": "DOWN", "confidence": "High"}
    elif final_gravity < -2:
        return {"signal": "SELL", "direction": "DOWN", "confidence": "Medium"}
    elif final_gravity < 0:
        return {"signal": "WEAK SELL", "direction": "DOWN", "confidence": "Low"}
    else:
        return {"signal": "HOLD", "direction": "FLAT", "confidence": "Neutral"}

def sequential_hybrid_analysis():
    """Execute sequential day-by-day hybrid analysis as production runs"""
    
    print("\n" + "=" * 100)
    print("SEQUENTIAL DAY-BY-DAY HYBRID ANALYSIS - PRODUCTION SIMULATION")
    print("=" * 100)
    print("Executing 11-day sequence with full pipeline per trading day")
    print("Formula: Final_Gravity = (Info_Gravity × 0.6) + (Technical_Score × 0.4)")
    print("=" * 100)
    
    # Initialize components
    db = DatabaseManager()
    sentiment_agent = SentimentAgent()
    orchestrator = OrchestratorAgent()
    market_fetcher = MarketDataFetcher()
    
    # Results tracking
    daily_results = []
    cumulative_stats = {
        "total_predictions": 0,
        "correct_directions": 0,
        "grade_distribution": {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
        "signal_distribution": {"STRONG BUY": 0, "BUY": 0, "WEAK BUY": 0, "HOLD": 0, 
                              "WEAK SELL": 0, "SELL": 0, "STRONG SELL": 0}
    }
    
    print(f"\n🚀 STARTING SEQUENTIAL ANALYSIS OF {len(SEQUENTIAL_DATES)} TRADING DAYS")
    print(f"Period: {SEQUENTIAL_DATES[0]} to {SEQUENTIAL_DATES[-1]}")
    
    for i, current_date in enumerate(SEQUENTIAL_DATES, 1):
        print(f"\n{'='*80}")
        print(f"PRODUCTION RUN {i}/{len(SEQUENTIAL_DATES)}: {current_date}")
        print(f"{'='*80}")
        
        try:
            # Get market data for current date
            daily_data = db.get_daily_data(current_date)
            if not daily_data:
                print(f"❌ No market data found for {current_date}")
                continue
            
            current_close = float(daily_data.get('close_price', 0))
            print(f"📊 Market Data: Close = ${current_close:.2f}")
            
            # STEP 1: Fresh Informational Gravity (Skeptical Constraints)
            print(f"\n🧠 STEP 1: FRESH INFORMATIONAL GRAVITY ANALYSIS")
            print("-" * 60)
            
            articles = db.get_articles_for_date(current_date)
            company_articles = []
            macro_articles = []
            
            if not articles:
                print(f"⚠️  No articles found for {current_date}")
                info_gravity = 0.0
                company_sentiment = 0.0
                macro_sentiment = 0.0
            else:
                print(f"📰 Found {len(articles)} articles for analysis")
                
                # Separate company and macro articles
                company_articles = [a for a in articles if a.get('article_type') == 'company']
                macro_articles = [a for a in articles if a.get('article_type') == 'macro']
                print(f"   Company: {len(company_articles)}, Macro: {len(macro_articles)}")
                
                # Fresh sentiment analysis with Skeptical Constraints
                sentiment_result = sentiment_agent.analyze_articles_by_type(
                    company_articles, macro_articles
                )
                
                info_gravity = sentiment_result.get('combined_score', 0.0)
                company_sentiment = sentiment_result.get('company_sentiment', 0.0) 
                macro_sentiment = sentiment_result.get('macro_sentiment', 0.0)
                
                print(f"✓ Informational Gravity: {info_gravity:+.2f}")
                print(f"  Company Sentiment: {company_sentiment:+.2f}")
                print(f"  Macro Sentiment: {macro_sentiment:+.2f}")
                
                # Update database with fresh sentiment
                success = db.update_sentiment_score(current_date, info_gravity)
                print(f"💾 Database Updated: {'✓' if success else '❌'}")
            
            # STEP 2: Technical Friction Capture
            print(f"\n⚙️ STEP 2: TECHNICAL FRICTION CAPTURE (14-day lookback)")
            print("-" * 60)
            
            technical_data = market_fetcher.fetch_technical_data(current_date)
            if technical_data:
                technical_score = technical_data['technical_score']
                rsi = technical_data['rsi']
                momentum = technical_data['momentum_3d']
                ma_position = technical_data['ma_position']
                
                print(f"✓ Technical Score: {technical_score:+.2f}")
                print(f"  RSI: {rsi:.1f} ({technical_data['rsi_pressure']})")
                print(f"  3D Momentum: {momentum:+.1f}% ({technical_data['momentum_direction']})")
                print(f"  MA Position: {ma_position}")
            else:
                print(f"⚠️  No technical data available")
                technical_score = 0.0
                rsi, momentum, ma_position = None, None, None
            
            # STEP 3: Hybrid Fusion with Dynamic Weights
            print(f"\n🔬 STEP 3: HYBRID FUSION")
            print("-" * 60)
            
            # Prepare news summary for dynamic weight determination
            news_summary = {
                'final_sentiment': info_gravity,
                'company_count': len(company_articles) if articles else 0,
                'macro_count': len(macro_articles) if articles else 0,
                'company_sentiment': company_sentiment,
                'macro_sentiment': macro_sentiment
            }
            
            # Use orchestrator's dynamic hybrid calculation
            hybrid_result = orchestrator.calculate_hybrid_signal(current_date, info_gravity, news_summary)
            
            final_gravity = hybrid_result.get('final_gravity', info_gravity)
            strategy_weights = hybrid_result.get('strategy_weights', {})
            signal_data = get_prediction_signal(final_gravity)
            
            print(f"📊 HYBRID CALCULATION (DYNAMIC WEIGHTS):")
            sentiment_weight = strategy_weights.get('sentiment', 0.6)
            technical_weight = strategy_weights.get('technical', 0.4)
            print(f"   Info Gravity ({sentiment_weight:.0%}):   {info_gravity:+.2f}")
            print(f"   Technical Score ({technical_weight:.0%}): {technical_score:+.2f}") 
            print(f"   Final Gravity:         {final_gravity:+.2f}")
            print(f"   Prediction Signal:     {signal_data['signal']}")
            print(f"   Direction:             {signal_data['direction']}")
            print(f"   Confidence:            {signal_data['confidence']}")
            
            # Show strategy analysis
            if strategy_weights:
                print(f"\n🧠 STRATEGY ANALYSIS:")
                print(f"   Regime: {strategy_weights.get('regime_analysis', 'N/A')}")
                print(f"   Dynamic Weights: Sentiment {sentiment_weight:.0%} | Technical {technical_weight:.0%}")
                print(f"   Reasoning: {strategy_weights.get('strategic_reasoning', 'N/A')[:100]}...")
            
            # STEP 4: Truth Confrontation (The Gap)
            print(f"\n⚔️ STEP 4: TRUTH CONFRONTATION")
            print("-" * 60)
            
            next_trading_day = get_next_trading_day(current_date, SEQUENTIAL_DATES)
            if next_trading_day:
                next_data = db.get_daily_data(next_trading_day)
                if next_data:
                    next_open = float(next_data.get('open_price', current_close))
                    gap_data = calculate_opening_gap(current_close, next_open)
                    
                    print(f"📈 ACTUAL GAP TO {next_trading_day}:")
                    print(f"   Previous Close: ${current_close:.2f}")
                    print(f"   Next Open: ${next_open:.2f}")
                    print(f"   Gap: {gap_data['gap_percent']:+.2f}% ({gap_data['gap_direction']})")
                    print(f"   Magnitude: {gap_data['gap_magnitude']}")
                    
                    # Grade the prediction
                    grade_data = grade_prediction_accuracy(
                        signal_data['direction'], gap_data['gap_direction'],
                        abs(final_gravity), abs(gap_data['gap_percent'])
                    )
                    
                    print(f"\n🎯 PREDICTION ACCURACY:")
                    print(f"   Grade: {grade_data['grade']} ({grade_data['score']:.1%})")
                    print(f"   {grade_data['description']}")
                    print(f"   Direction Correct: {'✅' if grade_data['direction_correct'] else '❌'}")
                    
                else:
                    print(f"⚠️  No market data for next day {next_trading_day}")
                    gap_data = {"gap_percent": 0, "gap_direction": "UNKNOWN", "gap_magnitude": "NONE"}
                    grade_data = {"grade": "N/A", "score": 0, "description": "No data for comparison"}
            else:
                print(f"⚠️  No next trading day available")
                gap_data = {"gap_percent": 0, "gap_direction": "UNKNOWN", "gap_magnitude": "NONE"}
                grade_data = {"grade": "N/A", "score": 0, "description": "End of sequence"}
            
            # STEP 5: Logging & Store Results
            daily_result = {
                "date": current_date,
                "close_price": current_close,
                "info_gravity": info_gravity,
                "company_sentiment": company_sentiment,
                "macro_sentiment": macro_sentiment,
                "technical_score": technical_score,
                "final_gravity": final_gravity,
                "prediction_signal": signal_data['signal'],
                "prediction_direction": signal_data['direction'],
                "prediction_confidence": signal_data['confidence'],
                "actual_gap_percent": gap_data.get('gap_percent', 0),
                "actual_gap_direction": gap_data.get('gap_direction', 'UNKNOWN'),
                "actual_gap_magnitude": gap_data.get('gap_magnitude', 'NONE'),
                "grade": grade_data.get('grade', 'N/A'),
                "accuracy_score": grade_data.get('score', 0),
                "direction_correct": grade_data.get('direction_correct', False),
                "next_trading_day": next_trading_day,
                "articles_analyzed": len(articles) if articles else 0,
                "sentiment_weight": strategy_weights.get('sentiment', 0.6),
                "technical_weight": strategy_weights.get('technical', 0.4),
                "strategy_regime": strategy_weights.get('regime_analysis', 'N/A'),
                "rsi": rsi,
                "momentum": momentum,
                "ma_position": ma_position
            }
            
            daily_results.append(daily_result)
            
            # Update cumulative statistics
            if grade_data.get('grade') != 'N/A':
                cumulative_stats["total_predictions"] += 1
                if grade_data.get('direction_correct'):
                    cumulative_stats["correct_directions"] += 1
                cumulative_stats["grade_distribution"][grade_data['grade']] += 1
            
            cumulative_stats["signal_distribution"][signal_data['signal']] += 1
            
            print(f"\n📋 STEP 5: DAILY SUMMARY")
            print("-" * 60)
            print(f"   Final Gravity: {final_gravity:+.2f}")
            print(f"   Signal: {signal_data['signal']}")
            print(f"   Grade: {grade_data.get('grade', 'N/A')}")
            print(f"   Articles: {len(articles) if articles else 0}")
            
            # Wait before next iteration
            if i < len(SEQUENTIAL_DATES):
                print(f"\n⏳ Waiting 2 seconds before next production run...")
                time.sleep(2)
                
        except Exception as e:
            print(f"❌ Error processing {current_date}: {str(e)}")
            continue
    
    # Final Cumulative Success Matrix
    print(f"\n{'='*100}")
    print("CUMULATIVE SUCCESS MATRIX - HYBRID SYSTEM EVOLUTION")
    print(f"{'='*100}")
    
    if daily_results:
        print(f"\n📊 PERFORMANCE SUMMARY:")
        print(f"   Total Production Runs: {len(daily_results)}")
        print(f"   Predictions Made: {cumulative_stats['total_predictions']}")
        if cumulative_stats['total_predictions'] > 0:
            direction_accuracy = cumulative_stats['correct_directions'] / cumulative_stats['total_predictions']
            print(f"   Direction Accuracy: {direction_accuracy:.1%}")
        
        print(f"\n🎯 GRADE DISTRIBUTION:")
        for grade, count in cumulative_stats['grade_distribution'].items():
            if count > 0:
                percentage = (count / cumulative_stats['total_predictions']) * 100 if cumulative_stats['total_predictions'] > 0 else 0
                print(f"   Grade {grade}: {count} predictions ({percentage:.1f}%)")
        
        print(f"\n📈 SIGNAL DISTRIBUTION:")
        for signal, count in cumulative_stats['signal_distribution'].items():
            if count > 0:
                percentage = (count / len(daily_results)) * 100
                print(f"   {signal}: {count} times ({percentage:.1f}%)")
        
        print(f"\n📋 DETAILED DAY-BY-DAY RESULTS:")
        print(f"{'Date':<12} {'Info':<6} {'Tech':<6} {'Final':<6} {'S/T Weights':<12} {'Signal':<12} {'Actual':<6} {'Grade':<5} {'Articles':<8}")
        print("-" * 100)
        
        for result in daily_results:
            articles_count = result['articles_analyzed']
            weight_str = f"{result['sentiment_weight']:.1f}/{result['technical_weight']:.1f}"
            print(f"{result['date']:<12} {result['info_gravity']:+5.1f} {result['technical_score']:+5.1f} "
                  f"{result['final_gravity']:+5.1f} {weight_str:<12} {result['prediction_signal']:<12} "
                  f"{result['actual_gap_direction']:<6} {result['grade']:<5} {articles_count:<8}")
        
        # Calculate average scores
        avg_info_gravity = sum(r['info_gravity'] for r in daily_results) / len(daily_results)
        avg_technical_score = sum(r['technical_score'] for r in daily_results) / len(daily_results)
        avg_final_gravity = sum(r['final_gravity'] for r in daily_results) / len(daily_results)
        avg_sentiment_weight = sum(r['sentiment_weight'] for r in daily_results) / len(daily_results)
        avg_technical_weight = sum(r['technical_weight'] for r in daily_results) / len(daily_results)
        
        print("-" * 100)
        print(f"{'AVERAGES':<12} {avg_info_gravity:+5.1f} {avg_technical_score:+5.1f} {avg_final_gravity:+5.1f} "
              f"{avg_sentiment_weight:.1f}/{avg_technical_weight:.1f}{'':>20}")
        
        print(f"\n🎯 DYNAMIC WEIGHT ANALYSIS:")
        weight_variations = [(r['sentiment_weight'], r['technical_weight'], r['date']) for r in daily_results]
        min_sentiment = min(r['sentiment_weight'] for r in daily_results)
        max_sentiment = max(r['sentiment_weight'] for r in daily_results)
        
        print(f"   Average Weights: Sentiment {avg_sentiment_weight:.1%} | Technical {avg_technical_weight:.1%}")
        print(f"   Weight Range: Sentiment [{min_sentiment:.1%} - {max_sentiment:.1%}]")
        
        # Count unique weight combinations
        unique_weights = set((r['sentiment_weight'], r['technical_weight']) for r in daily_results)
        print(f"   Unique Weight Combinations: {len(unique_weights)}")
        
        if len(unique_weights) > 1:
            print("   ✅ DYNAMIC WEIGHTING ACTIVE - System adapted to market conditions")
        else:
            print("   ⚠️  STATIC WEIGHTS - All days used same weightings")
        
        print(f"\n🔬 HYBRID SYSTEM EVOLUTION INSIGHTS:")
        realistic_scores = sum(1 for r in daily_results if abs(r['info_gravity']) <= 10)
        print(f"   Realistic Info Gravity Scores: {realistic_scores}/{len(daily_results)} ({realistic_scores/len(daily_results)*100:.1f}%)")
        
        strong_signals = sum(1 for r in daily_results if 'STRONG' in r['prediction_signal'])
        print(f"   Strong Conviction Signals: {strong_signals}/{len(daily_results)} ({strong_signals/len(daily_results)*100:.1f}%)")
        
        if cumulative_stats['total_predictions'] > 0:
            success_rate = cumulative_stats['correct_directions'] / cumulative_stats['total_predictions']
            if success_rate >= 0.6:
                print(f"   ✅ SYSTEM STATUS: SUCCESSFUL (Direction Accuracy: {success_rate:.1%})")
            else:
                print(f"   ⚠️  SYSTEM STATUS: NEEDS IMPROVEMENT (Direction Accuracy: {success_rate:.1%})")
    else:
        print("❌ No results to analyze")

if __name__ == "__main__":
    sequential_hybrid_analysis()