"""
NVIDIA Stock Prediction System - Main Entry Point
Runs the daily workflow to collect market data, news, and sentiment
"""

import sys
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo
from agents.orchestrator_agent import OrchestratorAgent
from utils.logger import setup_logger, log_section_header
from config.settings import validate_config, get_config_info

logger = setup_logger("main")


def main():
    """Main entry point for the NVIDIA stock prediction system"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="NVIDIA Stock Prediction System - Daily Workflow"
    )
    parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='Date to process (YYYY-MM-DD format, default: today)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without saving to database (for testing)'
    )
    parser.add_argument(
        '--calibrate',
        action='store_true',
        help='Run post-market gravity accuracy calibration'
    )
    parser.add_argument(
        '--info',
        action='store_true',
        help='Show system configuration and exit'
    )
    
    args = parser.parse_args()
    
    # Show configuration if requested
    if args.info:
        print_system_info()
        return 0
    
    # Run post-market calibration if requested
    if args.calibrate:
        return run_post_market_calibration()
    
    # Display header
    log_section_header(logger, "NVIDIA Stock Prediction System")
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.dry_run:
        logger.info("⚠️  DRY RUN MODE - No database writes")
    
    try:
        # Validate configuration
        logger.info("\nValidating configuration...")
        validate_config()
        logger.info("✓ Configuration valid")
        
        # ── Smart Temporal Integrity Patch ──
        # Backfill any missing next_day_open / next_day_close before workflow
        from data.database_manager import DatabaseManager
        logger.info("\n🔧 Running next-day backfill check...")
        _db = DatabaseManager()
        backfill_stats = _db.backfill_next_day_results()
        if backfill_stats["filled"] > 0:
            logger.info(f"✓ Backfilled {backfill_stats['filled']} rows")
        else:
            logger.info("✓ No gaps — temporal integrity OK")
        del _db
        
        # Initialize orchestrator
        logger.info("\nInitializing orchestrator...")
        orchestrator = OrchestratorAgent()
        logger.info("✓ Orchestrator ready")
        
        # Run daily workflow
        # Use US Eastern Time for the target date (market operates in ET)
        if args.date:
            target_date = args.date
        else:
            et_now = datetime.now(ZoneInfo("America/New_York"))
            target_date = et_now.strftime("%Y-%m-%d")
        
        logger.info(f"\nRunning workflow for {target_date}...")
        
        result = orchestrator.run_daily_workflow(
            date=target_date,
            dry_run=args.dry_run
        )
        
        # Display results
        print_workflow_results(result)
        
        # Determine exit code
        if result['success']:
            logger.info("\n✓ Workflow completed successfully")
            return 0
        else:
            logger.error("\n✗ Workflow failed")
            if result.get('errors'):
                for error in result['errors']:
                    logger.error(f"  - {error}")
            return 1
            
    except ValueError as e:
        # Configuration errors
        logger.error(f"\n✗ Configuration error: {str(e)}")
        logger.error("\nPlease check your .env file and ensure:")
        logger.error("  - OPENAI_API_KEY is set")
        logger.error("  - SERPER_API_KEY is set")
        logger.error("  - DB_PASSWORD is set")
        return 1
        
    except Exception as e:
        # Unexpected errors
        logger.error(f"\n✗ Unexpected error: {str(e)}", exc_info=True)
        return 1
    
    finally:
        logger.info(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60)


def run_post_market_calibration():
    """Run post-market gravity accuracy calibration
    
    Compares previous gravity predictions against actual market results
    and calculates accuracy + grade for each.
    """
    from data.database_manager import DatabaseManager
    from utils.analysis_utils import calculate_gravity_accuracy, get_accuracy_grade
    
    logger.info("="*60)
    logger.info("POST-MARKET GRAVITY CALIBRATION")
    logger.info("="*60)
    
    db = DatabaseManager()
    
    # Get predictions that need calibration
    predictions = db.get_predictions_for_accuracy_calculation(limit=30)
    
    if not predictions:
        logger.info("No predictions need calibration (all up to date)")
        return 0
    
    logger.info(f"Found {len(predictions)} predictions to calibrate")
    calibrated = 0
    
    for pred in predictions:
        date = str(pred['date'])
        sentiment_score = float(pred['sentiment_score'])
        price_change = float(pred['price_change_percent'])
        
        # Calculate accuracy
        accuracy = calculate_gravity_accuracy(sentiment_score, price_change)
        grade = get_accuracy_grade(accuracy)
        
        # Save to database (update_gravity_accuracy now saves both accuracy and grade)
        success = db.update_gravity_accuracy(date, accuracy)
        
        if success:
            calibrated += 1
            logger.info(f"  {date}: Accuracy={accuracy:.1f}% Grade={grade} "
                       f"(predicted={sentiment_score:+.1f}, actual={price_change:+.2f}%)")
        else:
            logger.error(f"  {date}: Failed to update")
    
    logger.info(f"\nCalibrated {calibrated}/{len(predictions)} predictions")
    logger.info("="*60)
    return 0


def print_system_info():
    """Print system configuration information"""
    config = get_config_info()
    
    print("\n" + "="*60)
    print("SYSTEM CONFIGURATION")
    print("="*60)
    print(f"\nStock Symbol: {config['stock_symbol']}")
    print(f"GPT Model: {config['gpt_model']}")
    print(f"Max Articles: {config['max_articles']}")
    print(f"Timezone: {config['timezone']}")
    print(f"Log Level: {config['log_level']}")
    print(f"\nDatabase:")
    print(f"  Host: {config['db_host']}")
    print(f"  Database: {config['db_name']}")
    print(f"\nAPI Keys:")
    print(f"  OpenAI: {'✓ Set' if config['openai_key_set'] else '✗ Not set'}")
    print(f"  Serper: {'✓ Set' if config['serper_key_set'] else '✗ Not set'}")
    print("="*60)


def print_workflow_results(result: dict):
    """Print workflow results summary"""
    print("\n" + "="*60)
    print("WORKFLOW RESULTS")
    print("="*60)
    print(f"\nTrading Day: {result['date']}")
    if result.get('ny_today'):
        print(f"News Date: {result['ny_today']}")
    print(f"Status: {'✓ SUCCESS' if result['success'] else '✗ FAILED'}")
    
    print(f"\nData Collection:")
    if result.get('market_data_existed'):
        print(f"  Market Data: ✓ (already in database)")
    else:
        print(f"  Market Data: {'✓ (newly fetched)' if result['market_data_collected'] else '✗'}")
    print(f"  Articles: {result['articles_collected']}")
    
    print(f"\nSentiment Analysis:")
    print(f"  Company: {result.get('company_sentiment', 0):.2f}")
    print(f"  Macro: {result.get('macro_sentiment', 0):.2f}")
    print(f"  Combined: {result['sentiment_score']:.2f}/100")
    print(f"  Confidence: {result['sentiment_confidence']}")
    
    # Prediction section
    print(f"\n" + "-"*60)
    print("HYBRID PREDICTION (DYNAMIC STRATEGY)")
    print("-"*60)
    
    # Primary prediction from hybrid system
    hybrid_signal = result.get('hybrid_prediction')
    hybrid_confidence = result.get('hybrid_confidence', 'N/A')
    hybrid_gravity = result.get('hybrid_final_gravity', 0.0)
    strategy_weights = result.get('strategy_weights', {})
    
    if hybrid_signal:
        if 'BUY' in hybrid_signal:
            print(f"\n  📈 HYBRID SIGNAL: {hybrid_signal}")
        elif 'SELL' in hybrid_signal:
            print(f"\n  📉 HYBRID SIGNAL: {hybrid_signal}")
        else:
            print(f"\n  ⚪ HYBRID SIGNAL: {hybrid_signal}")
        
        print(f"  Final Gravity: {hybrid_gravity:+.2f}")
        print(f"  Confidence: {hybrid_confidence}")
        print(f"  Strategy: Sentiment {strategy_weights.get('sentiment', 0.6):.0%} | Technical {strategy_weights.get('technical', 0.4):.0%}")
    else:
        print(f"\n  ⚠️  Hybrid prediction not available")
    
    # Secondary ML prediction (if available)
    print(f"\n" + "-"*60)
    print("ML PREDICTION (VALIDATION)")
    print("-"*60)
    
    if result.get('can_predict'):
        prediction = result.get('prediction', 'N/A')
        confidence = result.get('prediction_confidence', 0)
        
        # Colorful prediction display
        if prediction == 'UP':
            print(f"\n  📈 ML PREDICTION: {prediction}")
        else:
            print(f"\n  📉 ML PREDICTION: {prediction}")
        
        print(f"  Confidence: {confidence:.1%}")
    else:
        message = result.get('prediction_message', 'Not available')
        print(f"\n  ⚠️  ML prediction not ready")
        print(f"  Reason: {message}")
    
    # Opening ML prediction
    print(f"\n" + "-"*60)
    print("ML OPENING PREDICTION (GAP UP/DOWN)")
    print("-"*60)
    
    if result.get('can_predict_opening'):
        opening_pred = result.get('opening_prediction', 'N/A')
        opening_conf = result.get('opening_confidence', 0)
        
        if 'UP' in str(opening_pred):
            print(f"\n  🌅📈 OPENING PREDICTION: {opening_pred}")
        else:
            print(f"\n  🌅📉 OPENING PREDICTION: {opening_pred}")
        
        print(f"  Confidence: {opening_conf:.1%}")
    else:
        opening_msg = result.get('opening_message', 'Not available')
        print(f"\n  ⚠️  Opening prediction not ready")
        print(f"  Reason: {opening_msg}")
    
    if result.get('errors'):
        print(f"\nErrors:")
        for error in result['errors']:
            print(f"  - {error}")
    
    print("="*60)


if __name__ == "__main__":
    sys.exit(main())
