"""
Market Data Fetcher for NVIDIA Stock
Fetches stock data from Yahoo Finance and calculates technical indicators
"""

import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
from typing import Dict, Optional
from config.settings import (
    STOCK_SYMBOL,
    RSI_PERIOD,
    MACD_FAST,
    MACD_SLOW,
    MACD_SIGNAL,
    MA_SHORT,
    MA_LONG
)
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MarketDataFetcher:
    """Fetch NVIDIA stock data and calculate technical indicators"""
    
    def __init__(self, symbol: str = STOCK_SYMBOL):
        """
        Initialize market data fetcher
        
        Args:
            symbol: Stock symbol (default: NVDA)
        """
        self.symbol = symbol
        self.ticker = yf.Ticker(symbol)
        logger.info(f"MarketDataFetcher initialized for {symbol}")
    
    def fetch_daily_data(self, date: Optional[str] = None, use_last_trading_day: bool = False) -> Optional[Dict]:
        """
        Fetch daily stock data for a specific date
        
        Args:
            date: Date in YYYY-MM-DD format (default: today)
            use_last_trading_day: If True and date has no data, fetch last trading day instead
        
        Returns:
            Dictionary with stock data and technical indicators, or None if failed
        """
        try:
            # Use today's date if not specified
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
            
            logger.info(f"Fetching market data for {self.symbol} on {date}")
            
            # Calculate date range (need extra days for technical indicators)
            # Get 300 days to calculate 200-day moving average
            end_date = datetime.strptime(date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=300)
            
            # Download data from Yahoo Finance
            df = self.ticker.history(
                start=start_date.strftime("%Y-%m-%d"),
                end=(end_date + timedelta(days=1)).strftime("%Y-%m-%d")
            )
            
            if df.empty:
                logger.error(f"No data returned for {self.symbol} (check symbol or date range)")
                return None
            
            # Remove timezone from index for easier date matching
            df.index = df.index.tz_localize(None)
            
            # Calculate technical indicators
            df = self._calculate_indicators(df)
            
            # Get data for the specific date
            target_date = pd.to_datetime(date)
            if target_date not in df.index:
                logger.warning(f"No data available for {date} (market might be closed)")
                
                # If requested, try to get last trading day instead
                if use_last_trading_day:
                    logger.info("Attempting to fetch last trading day instead...")
                    last_day = self.get_last_trading_day()
                    if last_day and last_day != date:
                        logger.info(f"Using last trading day: {last_day}")
                        return self.fetch_daily_data(last_day, use_last_trading_day=False)
                
                return None
            
            # Extract data for target date
            row = df.loc[target_date]
            
            # Prepare return data
            data = {
                "date": date,
                "open_price": round(float(row['Open']), 2),
                "close_price": round(float(row['Close']), 2),
                "high_price": round(float(row['High']), 2),
                "low_price": round(float(row['Low']), 2),
                "volume": int(row['Volume']),
                "rsi": round(float(row['RSI']), 2) if pd.notna(row['RSI']) else None,
                "macd": round(float(row['MACD']), 4) if pd.notna(row['MACD']) else None,
                "macd_signal": round(float(row['MACD_signal']), 4) if pd.notna(row['MACD_signal']) else None,
                "moving_avg_50": round(float(row['SMA_50']), 2) if pd.notna(row['SMA_50']) else None,
                "moving_avg_200": round(float(row['SMA_200']), 2) if pd.notna(row['SMA_200']) else None,
            }
            
            logger.info(f"Successfully fetched data for {date}: Close=${data['close_price']}, Volume={data['volume']:,}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            return None
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            DataFrame with added technical indicators
        """
        try:
            # RSI (Relative Strength Index)
            df['RSI'] = ta.rsi(df['Close'], length=RSI_PERIOD)
            
            # MACD (Moving Average Convergence Divergence)
            macd = ta.macd(df['Close'], fast=MACD_FAST, slow=MACD_SLOW, signal=MACD_SIGNAL)
            if macd is not None:
                df['MACD'] = macd[f'MACD_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}']
                df['MACD_signal'] = macd[f'MACDs_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}']
                df['MACD_hist'] = macd[f'MACDh_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}']
            
            # Simple Moving Averages
            df['SMA_50'] = ta.sma(df['Close'], length=MA_SHORT)
            df['SMA_200'] = ta.sma(df['Close'], length=MA_LONG)
            
            logger.debug(f"Calculated technical indicators for {len(df)} days")
            return df
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            return df
    
    def fetch_historical_data(self, days: int = 100) -> Optional[pd.DataFrame]:
        """
        Fetch historical data for multiple days
        
        Args:
            days: Number of days to fetch
        
        Returns:
            DataFrame with historical data and indicators
        """
        try:
            logger.info(f"Fetching {days} days of historical data for {self.symbol}")
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 300)  # Extra for indicators
            
            # Download data
            df = self.ticker.history(
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d")
            )
            
            if df.empty:
                logger.error("No historical data returned")
                return None
            
            # Remove timezone from index
            df.index = df.index.tz_localize(None)
            
            # Calculate indicators
            df = self._calculate_indicators(df)
            
            # Keep only requested number of days
            df = df.tail(days)
            
            logger.info(f"Fetched {len(df)} days of historical data")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            return None
    
    def get_latest_price(self) -> Optional[float]:
        """
        Get the latest stock price
        
        Returns:
            Current stock price or None if failed
        """
        try:
            data = self.ticker.history(period="1d")
            if not data.empty:
                price = float(data['Close'].iloc[-1])
                logger.info(f"Latest {self.symbol} price: ${price:.2f}")
                return price
            return None
        except Exception as e:
            logger.error(f"Error getting latest price: {str(e)}")
            return None
    
    def is_market_open(self, date: Optional[str] = None) -> bool:
        """
        Check if market was open on a specific date
        
        Args:
            date: Date in YYYY-MM-DD format (default: today)
        
        Returns:
            True if market was open, False otherwise
        """
        try:
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
            
            # Try to fetch data for that date
            target_date = datetime.strptime(date, "%Y-%m-%d")
            df = self.ticker.history(
                start=target_date.strftime("%Y-%m-%d"),
                end=(target_date + timedelta(days=1)).strftime("%Y-%m-%d")
            )
            
            is_open = not df.empty
            logger.info(f"Market {'was open' if is_open else 'was closed'} on {date}")
            return is_open
            
        except Exception as e:
            logger.error(f"Error checking market status: {str(e)}")
            return False
    
    def get_last_trading_day(self) -> Optional[str]:
        """
        Get the most recent trading day (handles weekends/holidays)
        
        Returns:
            Date string in YYYY-MM-DD format or None if error
        """
        try:
            # Get last 5 days of data to ensure we catch the last trading day
            df = self.ticker.history(period="5d")
            
            if df.empty:
                logger.error("Cannot determine last trading day - no data available")
                return None
            
            # Remove timezone and get the last date
            df.index = df.index.tz_localize(None)
            last_date = df.index[-1].strftime("%Y-%m-%d")
            
            logger.info(f"Last trading day: {last_date}")
            return last_date
            
        except Exception as e:
            logger.error(f"Error getting last trading day: {str(e)}")
            return None


# ============================================
# MODULE TEST
# ============================================
if __name__ == "__main__":
    """Test the market data fetcher"""
    from utils.logger import log_section_header, log_data_summary
    
    logger = setup_logger("test_market_data")
    log_section_header(logger, "Market Data Fetcher Test")
    
    # Initialize fetcher
    fetcher = MarketDataFetcher()
    
    # Test 1: Get latest price
    logger.info("Test 1: Getting latest price...")
    price = fetcher.get_latest_price()
    if price:
        logger.info(f"✓ Latest NVDA price: ${price:.2f}")
    
    # Test 2: Check if market is open today
    logger.info("\nTest 2: Checking market status...")
    is_open = fetcher.is_market_open()
    logger.info(f"✓ Market open today: {is_open}")
    
    # Test 3: Fetch today's data (or most recent trading day)
    logger.info("\nTest 3: Fetching daily data...")
    data = fetcher.fetch_daily_data()
    if data:
        logger.info("✓ Successfully fetched daily data:")
        log_data_summary(logger, data)
    
    # Test 4: Fetch 30 days of historical data
    logger.info("\nTest 4: Fetching 30 days of historical data...")
    hist_df = fetcher.fetch_historical_data(days=30)
    if hist_df is not None:
        logger.info(f"✓ Fetched {len(hist_df)} days of data")
        logger.info(f"  Date range: {hist_df.index[0].date()} to {hist_df.index[-1].date()}")
        logger.info(f"  Latest close: ${hist_df['Close'].iloc[-1]:.2f}")
        logger.info(f"  Latest RSI: {hist_df['RSI'].iloc[-1]:.2f}")
    
    logger.info("\n✓ Market Data Fetcher test complete!")
