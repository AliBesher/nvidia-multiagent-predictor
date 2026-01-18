"""
Logging configuration and utilities for NVIDIA Stock Prediction System
Provides centralized logging with file and console output
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from config.settings import LOG_LEVEL, LOG_FILE, LOG_FORMAT, LOG_DATE_FORMAT, LOGS_DIR


class CustomFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
    }

    def format(self, record):
        # Add color to level name for console
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def setup_logger(name: str = "nvidia_prediction", log_file: Path = LOG_FILE) -> logging.Logger:
    """
    Set up and configure logger with file and console handlers
    
    Args:
        name: Logger name
        log_file: Path to log file
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL.upper()))
    
    # Prevent duplicate handlers if logger already exists
    if logger.handlers:
        return logger
    
    # Create formatters
    file_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    console_formatter = CustomFormatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    
    # ============================================
    # FILE HANDLER - Write to log file
    # ============================================
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # ============================================
    # CONSOLE HANDLER - Output to console
    # ============================================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, LOG_LEVEL.upper()))
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger


def create_daily_log_file() -> Path:
    """
    Create a daily log file with current date
    Useful for keeping separate logs for each day's execution
    
    Returns:
        Path to daily log file
    """
    today = datetime.now().strftime("%Y-%m-%d")
    daily_log = LOGS_DIR / f"nvidia_prediction_{today}.log"
    return daily_log


def log_section_header(logger: logging.Logger, section_name: str):
    """
    Log a formatted section header for better readability
    
    Args:
        logger: Logger instance
        section_name: Name of the section
    """
    separator = "=" * 60
    logger.info(separator)
    logger.info(f"  {section_name}")
    logger.info(separator)


def log_data_summary(logger: logging.Logger, data_dict: dict):
    """
    Log a dictionary of data in a formatted way
    
    Args:
        logger: Logger instance
        data_dict: Dictionary to log
    """
    logger.info("Data Summary:")
    for key, value in data_dict.items():
        logger.info(f"  {key}: {value}")


def log_error_with_context(logger: logging.Logger, error: Exception, context: str = ""):
    """
    Log an error with additional context information
    
    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Additional context about where/when error occurred
    """
    logger.error(f"Error occurred: {str(error)}")
    if context:
        logger.error(f"Context: {context}")
    logger.error(f"Error type: {type(error).__name__}")
    
    # Log traceback for debugging
    import traceback
    logger.debug("Full traceback:")
    logger.debug(traceback.format_exc())


# ============================================
# DEFAULT LOGGER INSTANCE
# ============================================
# Create default logger for the application
default_logger = setup_logger()


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================
def info(message: str):
    """Log info message using default logger"""
    default_logger.info(message)


def debug(message: str):
    """Log debug message using default logger"""
    default_logger.debug(message)


def warning(message: str):
    """Log warning message using default logger"""
    default_logger.warning(message)


def error(message: str):
    """Log error message using default logger"""
    default_logger.error(message)


def critical(message: str):
    """Log critical message using default logger"""
    default_logger.critical(message)


# ============================================
# MODULE TEST
# ============================================
if __name__ == "__main__":
    """Test the logger"""
    test_logger = setup_logger("test_logger")
    
    log_section_header(test_logger, "Logger Test")
    test_logger.debug("This is a debug message")
    test_logger.info("This is an info message")
    test_logger.warning("This is a warning message")
    test_logger.error("This is an error message")
    test_logger.critical("This is a critical message")
    
    log_data_summary(test_logger, {
        "stock": "NVDA",
        "price": 500.25,
        "volume": 1000000,
        "sentiment": 75.5
    })
    
    try:
        raise ValueError("Test error for logging")
    except Exception as e:
        log_error_with_context(test_logger, e, "Testing error logging functionality")
    
    test_logger.info("Logger test complete! Check logs/ directory for output.")
