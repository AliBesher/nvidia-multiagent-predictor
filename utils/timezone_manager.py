"""
Timezone Manager for NVIDIA Stock Prediction System
Handles strict New York Time operations for financial accuracy
Provides timezone validation and utilities for consistent market calculations
"""

import pytz
from datetime import datetime
from typing import Tuple
from utils.logger import setup_logger

logger = setup_logger(__name__)

class TimezoneManager:
    """Centralized timezone management for consistent NY market time operations"""
    
    def __init__(self):
        """Initialize with primary timezone references"""
        # PRIMARY FINANCIAL TIMEZONE REFERENCE
        self.ny_tz = pytz.timezone('America/New_York')  # EST/EDT automatically handled
        self.israel_tz = pytz.timezone('Asia/Jerusalem')
        self.utc_tz = pytz.UTC
        
        # Validate timezone setup on initialization
        self.print_timezone_status()
    
    def print_timezone_status(self) -> None:
        """Print comprehensive timezone validation status"""
        now_utc = datetime.now(self.utc_tz)
        now_israel = now_utc.astimezone(self.israel_tz)
        now_ny = now_utc.astimezone(self.ny_tz)
        
        # Determine active trading day
        active_trading_day = now_ny.strftime('%Y-%m-%d')
        
        print(f"🌍 GLOBAL TIMEZONE VALIDATION:")
        print(f"   UTC Reference:       {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"   Israel Execution:    {now_israel.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"   NY Market Primary:   {now_ny.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"   Active Trading Day:  {active_trading_day}")
        print(f"   Market State:        {self.get_market_state()}")
        print()
        
        logger.info(f"Timezone Manager - UTC: {now_utc} | Israel: {now_israel} | NY: {now_ny}")
    
    def get_ny_now(self) -> datetime:
        """Get current datetime in New York timezone"""
        return datetime.now(self.ny_tz)
    
    def get_ny_trading_date(self) -> str:
        """Get current trading date in New York timezone (YYYY-MM-DD)"""
        return self.get_ny_now().strftime('%Y-%m-%d')
    
    def get_market_state(self) -> str:
        """Determine if market is currently open, closed, or pre/post market"""
        ny_now = self.get_ny_now()
        hour = ny_now.hour
        minute = ny_now.minute
        weekday = ny_now.weekday()  # 0=Monday, 6=Sunday
        
        # Weekend check
        if weekday >= 5:  # Saturday or Sunday
            return "WEEKEND_CLOSED"
        
        # Market hours: 9:30 AM - 4:00 PM ET
        market_open_minutes = 9 * 60 + 30  # 9:30 AM
        market_close_minutes = 16 * 60      # 4:00 PM
        current_minutes = hour * 60 + minute
        
        if current_minutes < market_open_minutes:
            return "PRE_MARKET"
        elif current_minutes > market_close_minutes:
            return "POST_MARKET"
        else:
            return "MARKET_OPEN"
    
    def get_timezone_comparison(self) -> Tuple[datetime, datetime, datetime]:
        """Get current time in all three key timezones"""
        now_utc = datetime.now(self.utc_tz)
        now_israel = now_utc.astimezone(self.israel_tz)
        now_ny = now_utc.astimezone(self.ny_tz)
        
        return now_israel, now_ny, now_utc
    
    def convert_to_ny_time(self, dt: datetime) -> datetime:
        """Convert any datetime to NY timezone"""
        if dt.tzinfo is None:
            # Assume UTC if no timezone info
            dt = self.utc_tz.localize(dt)
        
        return dt.astimezone(self.ny_tz)
    
    def is_trading_day(self, date_str: str = None) -> bool:
        """Check if given date (or today) is a trading day (weekday)"""
        if date_str is None:
            check_date = self.get_ny_now()
        else:
            # Parse date string and localize to NY timezone
            check_date = datetime.strptime(date_str, '%Y-%m-%d')
            check_date = self.ny_tz.localize(check_date)
        
        # Trading days are Monday (0) through Friday (4)
        return check_date.weekday() < 5
    
    def validate_temporal_physics_time(self, article_time: datetime) -> Tuple[float, bool]:
        """Validate article time and calculate age in hours with NY reference"""
        ny_now = self.get_ny_now()
        
        # Ensure article time has timezone info
        if article_time.tzinfo is None:
            # Assume UTC if no timezone
            article_time = self.utc_tz.localize(article_time)
        
        # Convert both to UTC for precise calculation
        ny_now_utc = ny_now.astimezone(self.utc_tz)
        article_time_utc = article_time.astimezone(self.utc_tz)
        
        # Calculate age in hours
        time_diff = ny_now_utc - article_time_utc
        age_hours = time_diff.total_seconds() / 3600
        
        # Validate: age should be positive (no future articles)
        is_valid = age_hours >= 0
        
        if not is_valid:
            logger.warning(f"Time paradox detected: Article time {article_time} is in future relative to NY time {ny_now}")
        
        return age_hours, is_valid


# Global timezone manager instance
timezone_manager = TimezoneManager()

# Convenience functions for quick access
def get_ny_now() -> datetime:
    """Get current New York time"""
    return timezone_manager.get_ny_now()

def get_ny_trading_date() -> str:
    """Get current NY trading date (YYYY-MM-DD)"""
    return timezone_manager.get_ny_trading_date()

def print_timezone_status() -> None:
    """Print current timezone validation status"""
    timezone_manager.print_timezone_status()

def get_market_state() -> str:
    """Get current market state"""
    return timezone_manager.get_market_state()