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
        '--info',
        action='store_true',
        help='Show system configuration and exit'
    )
    
    args = parser.parse_args()
    
    # Show configuration if requested
    if args.info:
        print_system_info()
        return 0
    
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
    print("PREDICTION FOR NEXT TRADING DAY")
    print("-"*60)
    
    if result.get('can_predict'):
        prediction = result.get('prediction', 'N/A')
        confidence = result.get('prediction_confidence', 0)
        
        # Colorful prediction display
        if prediction == 'UP':
            print(f"\n  📈 PREDICTION: {prediction}")
        else:
            print(f"\n  📉 PREDICTION: {prediction}")
        
        print(f"  Confidence: {confidence:.1%}")
    else:
        message = result.get('prediction_message', 'Not available')
        print(f"\n  ⚠️  Cannot predict yet")
        print(f"  Reason: {message}")
    
    if result.get('errors'):
        print(f"\nErrors:")
        for error in result['errors']:
            print(f"  - {error}")
    
    print("="*60)


if __name__ == "__main__":
    sys.exit(main())
