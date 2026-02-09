"""
Fix Grade F Sentiments - Force Re-analysis with Skeptical Constraints
Re-analyzes sentiment for test dates using new realistic scoring (±10 range)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator_agent import OrchestratorAgent
from agents.sentiment_agent import SentimentAgent
from data.database_manager import DatabaseManager
from utils.logger import setup_logger
import pandas as pd

logger = setup_logger(__name__)

# Dates that need sentiment re-analysis
TARGET_DATES = [
    "2026-01-27", "2026-01-28", "2026-01-29", "2026-01-30",
    "2026-02-02", "2026-02-05", "2026-02-06"
]

def fix_outdated_sentiments():
    """Re-analyze sentiment scores using Skeptical Constraints for realistic scoring"""
    
    print("\n" + "=" * 80)
    print("FIXING GRADE F SENTIMENTS - SKEPTICAL CONSTRAINTS RE-ANALYSIS")
    print("=" * 80)
    print("Problem: Database contains old unrealistic sentiment scores (+82.3, etc.)")
    print("Solution: Re-analyze using new Skeptical Constraints (±10 range)")
    print("=" * 80)
    
    db = DatabaseManager()
    sentiment_agent = SentimentAgent()
    orchestrator = OrchestratorAgent()
    
    results = []
    
    for date in TARGET_DATES:
        print(f"\n🔄 PROCESSING {date}")
        print("-" * 50)
        
        try:
            # Get current data from database
            daily_data = db.get_daily_data(date)
            if not daily_data:
                print(f"❌ No data found for {date}")
                continue
            
            # Get old sentiment score
            old_sentiment = float(daily_data.get('sentiment_score', 0.0))
            close_price = float(daily_data.get('close_price', 0))
            
            print(f"📊 Current Database Data:")
            print(f"   Old Sentiment Score: {old_sentiment:+.2f}")
            print(f"   Close Price: ${close_price:.2f}")
            
            # Get articles for this date
            print(f"\n📰 Fetching articles for {date}...")
            articles = db.get_articles_for_date(date)
            
            if not articles:
                print(f"❌ No articles found for {date}")
                continue
            
            print(f"✓ Found {len(articles)} articles")
            
            # Separate company and macro articles
            company_articles = [a for a in articles if a.get('article_type') == 'company']
            macro_articles = [a for a in articles if a.get('article_type') == 'macro']
            
            print(f"   Company articles: {len(company_articles)}")
            print(f"   Macro articles: {len(macro_articles)}")
            
            # Re-analyze sentiment using current Skeptical Constraints
            print(f"\n🧠 RE-ANALYZING SENTIMENT WITH SKEPTICAL CONSTRAINTS...")
            print("   Using new realistic scoring system (±10 range)")
            
            # Use the SentimentAgent's analyze_articles_by_type method
            sentiment_result = sentiment_agent.analyze_articles_by_type(
                company_articles, 
                macro_articles
            )
            
            if not sentiment_result:
                print(f"❌ Sentiment analysis failed for {date}")
                continue
            
            # Extract new realistic scores
            new_company_sentiment = sentiment_result.get('company_sentiment', 0.0)
            new_macro_sentiment = sentiment_result.get('macro_sentiment', 0.0)
            new_combined_sentiment = sentiment_result.get('combined_score', 0.0)
            
            print(f"\n📈 NEW SKEPTICAL SENTIMENT ANALYSIS:")
            print(f"   Company Sentiment: {new_company_sentiment:+.2f}")
            print(f"   Macro Sentiment:   {new_macro_sentiment:+.2f}")
            print(f"   Combined Score:    {new_combined_sentiment:+.2f}")
            
            print(f"\n⚖️  COMPARISON:")
            print(f"   OLD Score: {old_sentiment:+.2f} (unrealistic)")
            print(f"   NEW Score: {new_combined_sentiment:+.2f} (skeptical constraints)")
            print(f"   Difference: {old_sentiment - new_combined_sentiment:+.2f} points")
            
            if abs(new_combined_sentiment) <= 10:
                print(f"   ✅ NEW score is within ±10 realistic range")
            else:
                print(f"   ⚠️  NEW score still outside ±10 range - check prompt")
            
            # Update database with new realistic sentiment
            print(f"\n💾 UPDATING DATABASE...")
            success = db.update_sentiment_score(date, new_combined_sentiment)
            
            if success:
                print(f"✅ Database updated successfully")
                
                # Now test hybrid calculation with new score
                print(f"\n🔬 TESTING HYBRID WITH NEW SCORE...")
                hybrid_result = orchestrator.calculate_hybrid_signal(date, new_combined_sentiment)
                
                print(f"📊 NEW HYBRID ANALYSIS:")
                print(f"   Info Gravity (60%):    {hybrid_result['info_gravity']:+.2f}")
                print(f"   Technical Score (40%): {hybrid_result['technical_score']:+.2f}")
                print(f"   Final Hybrid Gravity:  {hybrid_result['final_gravity']:+.2f}")
                print(f"   Signal Alignment:      {hybrid_result['signal_alignment']}")
                print(f"   Confidence:            {hybrid_result['hybrid_confidence']}")
                print(f"   Recommendation:        {hybrid_result['recommendation']}")
                
                results.append({
                    'date': date,
                    'old_sentiment': old_sentiment,
                    'new_sentiment': new_combined_sentiment,
                    'difference': old_sentiment - new_combined_sentiment,
                    'technical_score': hybrid_result['technical_score'],
                    'final_gravity': hybrid_result['final_gravity'],
                    'confidence': hybrid_result['hybrid_confidence'],
                    'company_articles': len(company_articles),
                    'macro_articles': len(macro_articles)
                })
            else:
                print(f"❌ Failed to update database")
                
        except Exception as e:
            print(f"❌ Error processing {date}: {str(e)}")
            continue
    
    # Summary analysis
    if results:
        print("\n" + "=" * 80)
        print("SKEPTICAL CONSTRAINTS SUMMARY")
        print("=" * 80)
        
        print(f"📋 SENTIMENT SCORE COMPARISON:")
        print(f"{'Date':<12} {'Old Score':<10} {'New Score':<10} {'Change':<8} {'Articles':<10} {'Final Hybrid':<12}")
        print("-" * 80)
        
        total_old_avg = sum(r['old_sentiment'] for r in results) / len(results)
        total_new_avg = sum(r['new_sentiment'] for r in results) / len(results)
        
        for r in results:
            articles_total = r['company_articles'] + r['macro_articles']
            print(f"{r['date']:<12} {r['old_sentiment']:+8.1f} {r['new_sentiment']:+8.1f} "
                  f"{r['difference']:+6.1f} {articles_total:>8} {r['final_gravity']:+10.2f}")
        
        print("-" * 80)
        print(f"{'AVERAGE':<12} {total_old_avg:+8.1f} {total_new_avg:+8.1f} "
              f"{total_old_avg - total_new_avg:+6.1f}")
        
        print(f"\n🎯 SKEPTICAL CONSTRAINTS IMPACT:")
        print(f"   Average Old Score: {total_old_avg:+.1f} (unrealistic)")
        print(f"   Average New Score: {total_new_avg:+.1f} (skeptical)")
        print(f"   Average Reduction: {total_old_avg - total_new_avg:.1f} points")
        
        # Check if scores are now realistic
        realistic_scores = sum(1 for r in results if abs(r['new_sentiment']) <= 10)
        print(f"   Realistic Scores:  {realistic_scores}/{len(results)} within ±10 range")
        
        if realistic_scores == len(results):
            print(f"   ✅ SUCCESS: All scores now realistic!")
        else:
            print(f"   ⚠️  Some scores still need adjustment")
        
        print(f"\n🔬 HYBRID SYSTEM IMPROVEMENT:")
        print(f"   Technical Layer now receives realistic sentiment input")
        print(f"   Final gravity scores are properly balanced")
        print(f"   No need for additional normalization")
        
        # Show specific Jan 27 comparison as requested
        jan_27_result = next((r for r in results if r['date'] == '2026-01-27'), None)
        if jan_27_result:
            print(f"\n🎯 JANUARY 27 SPECIFIC COMPARISON (as requested):")
            print(f"   Old Score: {jan_27_result['old_sentiment']:+.1f}")
            print(f"   New Skeptical Score: {jan_27_result['new_sentiment']:+.1f}")
            print(f"   Reduction: {jan_27_result['difference']:.1f} points")
            print(f"   Final Hybrid: {jan_27_result['final_gravity']:+.2f}")
    else:
        print("\n❌ No results to analyze")

if __name__ == "__main__":
    fix_outdated_sentiments()