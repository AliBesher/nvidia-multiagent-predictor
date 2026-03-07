"""
Market Data Fetcher for NVIDIA Stock
Fetches stock data from Yahoo Finance and calculates technical indicators
Operates strictly on New York Time (EST/EDT) for financial accuracy
"""

import yfinance as yf
import pandas as pd
import pandas_ta as ta
import math
import numpy as np
from datetime import datetime, timedelta
import pytz
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
from utils.timezone_manager import get_ny_now, get_ny_trading_date
from datetime import date as date_class

logger = setup_logger(__name__)

logger = setup_logger(__name__)


class MarketDataFetcher:
    """Fetch NVIDIA stock data and calculate technical indicators with NY timezone reference"""
    
    def __init__(self, symbol: str = STOCK_SYMBOL):
        """
        Initialize market data fetcher with strict NY timezone reference
        
        Args:
            symbol: Stock symbol (default: NVDA)
        """
        self.symbol = symbol
        self.ticker = yf.Ticker(symbol)
        
        # PRIMARY TIMEZONE REFERENCE: New York (EST/EDT)
        self.ny_tz = pytz.timezone('America/New_York')
        
        # Print timezone validation for market data operations
        ny_now = get_ny_now()
        trading_date = get_ny_trading_date()
        
        print(f"📈 MARKET DATA FETCHER INITIALIZATION:")
        print(f"   Symbol:              {symbol}")
        print(f"   NY Market Time:      {ny_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"   Active Trading Day:  {trading_date}")
        print()
        
        logger.info(f"MarketDataFetcher initialized for {symbol} with NY timezone reference")
    
    def get_next_trading_session(self, start_date: Optional[str] = None) -> Optional[str]:
        """
        Permanent Market Holiday & Weekend Intelligence
        Find the next available trading session, skipping weekends and market holidays
        
        Args:
            start_date: Starting date in YYYY-MM-DD format (default: current NY date)
            
        Returns:
            Next trading session date in YYYY-MM-DD format
        """
        try:
            if start_date is None:
                current_date = get_ny_trading_date()
                start = datetime.strptime(current_date, '%Y-%m-%d').date()
            else:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
            
            # Market holidays for current and future years (core holidays)
            def get_market_holidays(year: int) -> set:
                """Get major market holidays for a given year"""
                holidays = set()
                
                # Fixed holidays
                holidays.add(date_class(year, 1, 1))   # New Year's Day
                holidays.add(date_class(year, 7, 4))   # Independence Day
                holidays.add(date_class(year, 12, 25)) # Christmas
                
                # Third Monday in January (MLK Day) 
                jan_1 = date_class(year, 1, 1)
                days_to_first_monday = (7 - jan_1.weekday()) % 7
                first_monday = jan_1 + timedelta(days=days_to_first_monday)
                mlk_day = first_monday + timedelta(days=14)  # Third Monday
                holidays.add(mlk_day)
                
                # Third Monday in February (Presidents Day)
                feb_1 = date_class(year, 2, 1)
                days_to_first_monday = (7 - feb_1.weekday()) % 7
                first_monday = feb_1 + timedelta(days=days_to_first_monday)
                presidents_day = first_monday + timedelta(days=14)  # Third Monday
                holidays.add(presidents_day)
                
                # Last Monday in May (Memorial Day)
                may_31 = date_class(year, 5, 31)
                days_back = may_31.weekday()  # 0=Monday, 6=Sunday
                memorial_day = may_31 - timedelta(days=days_back)
                holidays.add(memorial_day)
                
                # First Monday in September (Labor Day)
                sep_1 = date_class(year, 9, 1)
                days_to_first_monday = (7 - sep_1.weekday()) % 7
                labor_day = sep_1 + timedelta(days=days_to_first_monday)
                holidays.add(labor_day)
                
                # Fourth Thursday in November (Thanksgiving)
                nov_1 = date_class(year, 11, 1)
                days_to_first_thursday = (3 - nov_1.weekday()) % 7  # Thursday = 3
                first_thursday = nov_1 + timedelta(days=days_to_first_thursday)
                thanksgiving = first_thursday + timedelta(days=21)  # Fourth Thursday
                holidays.add(thanksgiving)
                
                return holidays
            
            # Get holidays for current and next year
            current_year = start.year
            market_holidays = get_market_holidays(current_year)
            market_holidays.update(get_market_holidays(current_year + 1))
            
            # Find next trading day
            current = start + timedelta(days=1)
            max_days_ahead = 10  # Safety limit
            days_checked = 0
            
            while days_checked < max_days_ahead:
                # Skip weekends (Saturday=5, Sunday=6)
                if current.weekday() >= 5:
                    current += timedelta(days=1)
                    days_checked += 1
                    continue
                    
                # Skip market holidays
                if current in market_holidays:
                    current += timedelta(days=1)
                    days_checked += 1
                    continue
                    
                # Found valid trading day
                next_session = current.strftime('%Y-%m-%d')
                logger.info(f"Next trading session after {start_date or start}: {next_session}")
                return next_session
            
            # Fallback if no trading day found within limit
            logger.error(f"Could not find next trading session within {max_days_ahead} days")
            return None
            
        except Exception as e:
            logger.error(f"Error finding next trading session: {str(e)}")
            return None
    
    def fetch_daily_data(self, date: Optional[str] = None, use_last_trading_day: bool = False) -> Optional[Dict]:
        """
        Fetch daily stock data for a specific date using NY timezone reference
        
        Args:
            date: Date in YYYY-MM-DD format (default: current NY trading date)
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
                # New indicators
                "bollinger_upper": round(float(row['BB_upper']), 2) if 'BB_upper' in row and pd.notna(row['BB_upper']) else None,
                "bollinger_lower": round(float(row['BB_lower']), 2) if 'BB_lower' in row and pd.notna(row['BB_lower']) else None,
                "bollinger_width": round(float(row['BB_width']), 2) if 'BB_width' in row and pd.notna(row['BB_width']) else None,
                "bollinger_pctb": round(float(row['BB_pctB']), 4) if 'BB_pctB' in row and pd.notna(row['BB_pctB']) else None,
                "atr": round(float(row['ATR']), 2) if 'ATR' in row and pd.notna(row['ATR']) else None,
                "atr_percent": round(float(row['ATR_pct']), 2) if 'ATR_pct' in row and pd.notna(row['ATR_pct']) else None,
                "volume_ratio": round(float(row['Volume_Ratio']), 2) if 'Volume_Ratio' in row and pd.notna(row['Volume_Ratio']) else None,
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
            
            # Bollinger Bands (20-period, 2 std dev)
            bbands = ta.bbands(df['Close'], length=20, std=2)
            if bbands is not None:
                # Find actual column names (varies by pandas_ta version)
                bb_cols = bbands.columns.tolist()
                bb_upper_col = [c for c in bb_cols if c.startswith('BBU')][0]
                bb_mid_col = [c for c in bb_cols if c.startswith('BBM')][0]
                bb_lower_col = [c for c in bb_cols if c.startswith('BBL')][0]
                df['BB_upper'] = bbands[bb_upper_col]
                df['BB_middle'] = bbands[bb_mid_col]
                df['BB_lower'] = bbands[bb_lower_col]
                # BB Width: measures volatility (wider = more volatile)
                df['BB_width'] = ((df['BB_upper'] - df['BB_lower']) / df['BB_middle']) * 100
                # BB %B: where price sits within bands (0=lower, 1=upper, >1=above upper)
                df['BB_pctB'] = (df['Close'] - df['BB_lower']) / (df['BB_upper'] - df['BB_lower'])
            
            # ATR - Average True Range (14-period) — measures volatility
            atr_result = ta.atr(df['High'], df['Low'], df['Close'], length=14)
            if atr_result is not None:
                df['ATR'] = atr_result
                # ATR as percentage of price (normalized for comparability)
                df['ATR_pct'] = (df['ATR'] / df['Close']) * 100
            
            # Volume Spike Detection: current volume vs 20-day average
            df['Volume_SMA_20'] = ta.sma(df['Volume'], length=20)
            df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA_20']
            
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
    
    def calculate_opening_gap(self, close_date: str, open_date: Optional[str] = None) -> Optional[Dict]:
        """
        Calculate opening gap using smart market logic
        Gap = Market_Open(Next_Available_Trading_Day) - Market_Close(Current_Day)
        
        Args:
            close_date: Date of closing price (YYYY-MM-DD)
            open_date: Date of opening price (default: auto-detect next trading session)
            
        Returns:
            Dictionary with gap analysis or None if failed
        """
        try:
            # Get next trading session if not specified
            if open_date is None:
                open_date = self.get_next_trading_session(close_date)
                if not open_date:
                    logger.error(f"Could not determine next trading session after {close_date}")
                    return None
            
            # Fetch closing data
            close_data = self.fetch_daily_data(close_date)
            if not close_data:
                logger.error(f"No closing data available for {close_date}")
                return None
                
            # Fetch opening data  
            open_data = self.fetch_daily_data(open_date)
            if not open_data:
                logger.error(f"No opening data available for {open_date}")
                return None
            
            close_price = close_data['close_price']
            open_price = open_data['open_price']
            gap_amount = open_price - close_price
            gap_percent = (gap_amount / close_price) * 100
            
            gap_analysis = {
                'close_date': close_date,
                'open_date': open_date,
                'close_price': close_price,
                'open_price': open_price,
                'gap_amount': gap_amount,
                'gap_percent': gap_percent,
                'direction': 'UP' if gap_amount > 0 else 'DOWN',
                'trading_days_skipped': self._count_calendar_days(close_date, open_date) - 1
            }
            
            logger.info(f"Gap Analysis: {close_date} close ${close_price:.2f} → {open_date} open ${open_price:.2f} = {gap_percent:+.2f}%")
            return gap_analysis
            
        except Exception as e:
            logger.error(f"Error calculating opening gap: {str(e)}")
            return None
    
    def _count_calendar_days(self, start_date: str, end_date: str) -> int:
        """Count calendar days between two dates"""
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        return (end - start).days
    
    def get_price_change_percent(self, start_date: str, end_date: str) -> Optional[float]:
        """
        Calculate price change percentage between two dates
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Price change percentage, or None if data not available
        """
        try:
            logger.info(f"Calculating price change from {start_date} to {end_date}")
            
            # Get data for both dates
            start_data = self.fetch_daily_data(start_date)
            end_data = self.fetch_daily_data(end_date)
            
            if not start_data or not end_data:
                logger.warning(f"Cannot calculate price change - missing data for {start_date} or {end_date}")
                return None
            
            start_price = float(start_data['close_price'])
            end_price = float(end_data['close_price'])
            
            if start_price == 0:
                logger.error("Start price is zero - cannot calculate percentage")
                return None
            
            price_change_percent = ((end_price - start_price) / start_price) * 100
            
            logger.info(f"Price change: ${start_price:.2f} -> ${end_price:.2f} ({price_change_percent:+.2f}%)")
            return round(price_change_percent, 2)
            
        except Exception as e:
            logger.error(f"Error calculating price change: {str(e)}")
            return None
    
    def fetch_technical_data(self, date: str, lookback_days: int = 14) -> Optional[Dict]:
        """
        Fetch technical analysis data for a specific date with lookback period
        
        Args:
            date: Date in YYYY-MM-DD format
            lookback_days: Number of days to look back for calculations
            
        Returns:
            Dictionary with technical indicators and analysis
        """
        try:
            logger.info(f"Fetching technical data for {date} with {lookback_days} day lookback")
            
            # Calculate extended date range for technical indicators
            end_date = datetime.strptime(date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=lookback_days + 100)  # Extra for moving averages
            
            # Download data
            df = self.ticker.history(
                start=start_date.strftime("%Y-%m-%d"),
                end=(end_date + timedelta(days=1)).strftime("%Y-%m-%d")
            )
            
            if df.empty:
                logger.error(f"No technical data available for {date}")
                return None
            
            # Remove timezone
            df.index = df.index.tz_localize(None)
            
            # Calculate indicators
            df = self._calculate_indicators(df)
            
            # Get target date data
            target_date = pd.to_datetime(date)
            if target_date not in df.index:
                logger.warning(f"No data for {date}, trying last available date")
                target_date = df.index[-1]
            
            row = df.loc[target_date]
            
            # Calculate 3-day momentum
            momentum_3d = self._calculate_momentum(df, target_date, 3)
            
            # Calculate distance from moving averages
            ma_distance = self._calculate_ma_distance(row)
            
            # Extract new indicator values
            bb_pctb = float(row['BB_pctB']) if 'BB_pctB' in row and pd.notna(row['BB_pctB']) else 0.5
            bb_width = float(row['BB_width']) if 'BB_width' in row and pd.notna(row['BB_width']) else 0.0
            atr_pct = float(row['ATR_pct']) if 'ATR_pct' in row and pd.notna(row['ATR_pct']) else 0.0
            volume_ratio = float(row['Volume_Ratio']) if 'Volume_Ratio' in row and pd.notna(row['Volume_Ratio']) else 1.0
            
            # Calculate technical score (-10 to +10) — Non-Linear Physics-Based Engine
            score_result = self._calculate_technical_score(
                row, momentum_3d, ma_distance, bb_pctb, bb_width, atr_pct, volume_ratio
            )
            technical_score = score_result['technical_score']
            confidence_level = score_result['confidence_level']
            score_breakdown = score_result['contribution_breakdown']
            
            technical_data = {
                "date": date,
                "close_price": round(float(row['Close']), 2),
                "rsi": round(float(row['RSI']), 2) if pd.notna(row['RSI']) else None,
                "momentum_3d": round(momentum_3d, 2),
                "ma_50_distance": round(ma_distance['ma50_dist'], 2),
                "ma_200_distance": round(ma_distance['ma200_dist'], 2),
                "technical_score": round(technical_score, 2),
                "confidence_level": round(confidence_level, 1),
                "score_breakdown": score_breakdown,
                "rsi_pressure": self._get_rsi_pressure(row['RSI']),
                "momentum_direction": "UP" if momentum_3d > 0 else "DOWN",
                "ma_position": ma_distance['position'],
                # New indicators for Strategy Agent
                "bollinger_pctb": round(bb_pctb, 4),
                "bollinger_width": round(bb_width, 2),
                "bollinger_position": "ABOVE_UPPER" if bb_pctb > 1.0 else "NEAR_UPPER" if bb_pctb > 0.8 else "MIDDLE" if bb_pctb > 0.2 else "NEAR_LOWER" if bb_pctb > 0.0 else "BELOW_LOWER",
                "atr_percent": round(atr_pct, 2),
                "volatility_level": "HIGH" if atr_pct > 3.0 else "MODERATE" if atr_pct > 1.5 else "LOW",
                "volume_ratio": round(volume_ratio, 2),
                "volume_signal": "SPIKE" if volume_ratio > 2.0 else "HIGH" if volume_ratio > 1.5 else "NORMAL" if volume_ratio > 0.7 else "DRY"
            }
            
            logger.info(f"Technical Analysis for {date}: Score={technical_score:+.2f} (Confidence={confidence_level:.0f}%), RSI={technical_data['rsi']}, Momentum={momentum_3d:+.2f}%, BB%B={bb_pctb:.2f}, ATR%={atr_pct:.1f}%, Vol={volume_ratio:.1f}x")
            return technical_data
            
        except Exception as e:
            logger.error(f"Error fetching technical data: {str(e)}")
            return None
    
    def _calculate_momentum(self, df: pd.DataFrame, target_date: pd.Timestamp, days: int = 3) -> float:
        """
        Calculate price momentum over specified number of days
        
        Args:
            df: DataFrame with price data
            target_date: Target date for calculation
            days: Number of days for momentum calculation
            
        Returns:
            Momentum percentage
        """
        try:
            # Find target date index
            target_idx = df.index.get_loc(target_date)
            
            if target_idx < days:
                # Not enough data, use available data
                start_idx = 0
            else:
                start_idx = target_idx - days
            
            start_price = df['Close'].iloc[start_idx]
            end_price = df['Close'].iloc[target_idx]
            
            momentum = ((end_price - start_price) / start_price) * 100
            return momentum
            
        except Exception as e:
            logger.warning(f"Error calculating momentum: {str(e)}")
            return 0.0
    
    def _calculate_ma_distance(self, row: pd.Series) -> Dict:
        """
        Calculate distance from moving averages
        
        Args:
            row: Single row of DataFrame with price and MA data
            
        Returns:
            Dictionary with MA distance information
        """
        try:
            close_price = float(row['Close'])
            
            # Distance from 50-day MA
            ma50_dist = 0.0
            if pd.notna(row['SMA_50']):
                ma50 = float(row['SMA_50'])
                ma50_dist = ((close_price - ma50) / ma50) * 100
            
            # Distance from 200-day MA
            ma200_dist = 0.0
            if pd.notna(row['SMA_200']):
                ma200 = float(row['SMA_200'])
                ma200_dist = ((close_price - ma200) / ma200) * 100
            
            # Determine position relative to MAs
            position = "unknown"
            if pd.notna(row['SMA_50']) and pd.notna(row['SMA_200']):
                if close_price > row['SMA_50'] > row['SMA_200']:
                    position = "bullish"
                elif close_price < row['SMA_50'] < row['SMA_200']:
                    position = "bearish"
                else:
                    position = "mixed"
            
            return {
                "ma50_dist": ma50_dist,
                "ma200_dist": ma200_dist,
                "position": position
            }
            
        except Exception as e:
            logger.warning(f"Error calculating MA distance: {str(e)}")
            return {"ma50_dist": 0.0, "ma200_dist": 0.0, "position": "unknown"}
    
    def _get_rsi_pressure(self, rsi: float) -> str:
        """
        Determine RSI pressure direction
        
        Args:
            rsi: RSI value
            
        Returns:
            Pressure direction string
        """
        if pd.isna(rsi):
            return "neutral"
        
        if rsi > 70:
            return "overbought"  # Negative pressure
        elif rsi < 30:
            return "oversold"    # Positive pressure
        else:
            return "neutral"
    
    def _calculate_technical_score(self, row: pd.Series, momentum: float, ma_distance: Dict,
                                    bb_pctb: float = 0.5, bb_width: float = 0.0,
                                    atr_pct: float = 0.0, volume_ratio: float = 1.0) -> Dict:
        """
        Non-Linear Physics-Based Technical Score Engine
        
        Instead of simple linear addition, uses:
          1. Volume as a Force Multiplier on Momentum (not additive)
          2. Smooth exponential RSI penalties (no hard thresholds)
          3. Bollinger + Volume context-aware breakout/reversion logic
          4. Logarithmic MA convergence (diminishing returns when overextended)
          5. Tanh normalization to squash into [-10, +10]
          6. ATR as Confidence metadata (not directional)
        
        Returns:
            Dict with 'technical_score' (-10 to +10), 'confidence_level' (0-100),
            and 'contribution_breakdown' dict
        """
        try:
            # ================================================================
            # 1. MOMENTUM × VOLUME FORCE (Non-Linear Interaction)
            # ================================================================
            # Base momentum with quadratic boost for breakouts
            abs_mom = abs(momentum)
            if abs_mom > 4.0:
                # Quadratic boost: breakout force accelerates
                boosted_mom = 4.0 + (abs_mom - 4.0) ** 1.5 * 0.5
                base_mom = math.copysign(boosted_mom, momentum)
            else:
                base_mom = momentum
            
            # Volume as force multiplier: sqrt(volume_ratio)
            # vol_ratio=1.0 → multiplier=1.0 (neutral)
            # vol_ratio=2.0 → multiplier=1.41 (amplify)
            # vol_ratio=0.5 → multiplier=0.71 (dampen)
            vol_multiplier = math.sqrt(max(volume_ratio, 0.1))
            
            # Momentum × Volume Force
            momentum_force = base_mom * vol_multiplier * 0.6  # Weight factor
            
            # ================================================================
            # 2. RSI SMOOTH PENALTY (Exponential, no hard thresholds)
            # ================================================================
            rsi_score = 0.0
            if pd.notna(row['RSI']):
                rsi = float(row['RSI'])
                # Center around 50, apply smooth exponential penalty
                # For NVIDIA: use 75/25 thresholds (high-volatility stock)
                if rsi > 50:
                    # Overbought penalty: grows exponentially past 75
                    overshoot = max(0, rsi - 75)
                    rsi_score = -(overshoot ** 1.8) / 200  # Smooth exponential
                    # Mild positive for 50-65 range (healthy bullish momentum)
                    if rsi < 65:
                        rsi_score = (rsi - 50) * 0.02  # Slight positive
                elif rsi < 50:
                    # Oversold bounce: grows exponentially below 25
                    undershoot = max(0, 25 - rsi)
                    rsi_score = (undershoot ** 1.8) / 200  # Smooth exponential
                    # Mild negative for 35-50 range (weakening)
                    if rsi > 35:
                        rsi_score = -(50 - rsi) * 0.02
            
            # ================================================================
            # 3. BOLLINGER BANDS — Context-Aware (Volume interaction)
            # ================================================================
            bb_score = 0.0
            
            if bb_pctb > 1.0:
                # Price ABOVE upper band
                if volume_ratio > 1.3:
                    # High volume + above band = TREND CONTINUATION (Bullish)
                    bb_score = min(2.0, (bb_pctb - 1.0) * 3.0)
                else:
                    # Low volume + above band = REVERSION RISK (Bearish)
                    bb_score = -min(1.5, (bb_pctb - 1.0) * 4.0)
            elif bb_pctb < 0.0:
                # Price BELOW lower band
                if volume_ratio > 1.3:
                    # High volume + below band = PANIC SELLING (more downside)
                    bb_score = -min(2.0, abs(bb_pctb) * 3.0)
                else:
                    # Low volume + below band = BOUNCE CANDIDATE (Bullish)
                    bb_score = min(1.5, abs(bb_pctb) * 4.0)
            else:
                # Inside bands: mild mean reversion toward 0.5
                # Closer to edges = mild signal
                if bb_pctb > 0.75:
                    bb_score = -0.3 * (bb_pctb - 0.75) / 0.25
                elif bb_pctb < 0.25:
                    bb_score = 0.3 * (0.25 - bb_pctb) / 0.25
            
            # ================================================================
            # 4. MOVING AVERAGE CONVERGENCE (Logarithmic Scaling)
            # ================================================================
            ma_score = 0.0
            ma50_dist = ma_distance['ma50_dist']
            ma200_dist = ma_distance['ma200_dist']
            
            # Logarithmic: good returns near MA, diminishing when overextended
            # sign(dist) × ln(1 + |dist|) — capped at ~2.5
            if abs(ma50_dist) > 0.1:
                log_ma50 = math.copysign(
                    math.log1p(abs(ma50_dist)) * 0.8,  # log(1+|x|) × weight
                    ma50_dist
                )
                # Gravitational pull: penalize extreme extension
                if abs(ma50_dist) > 8:
                    pull = (abs(ma50_dist) - 8) * 0.1
                    log_ma50 -= math.copysign(pull, ma50_dist)
                ma_score += min(2.0, max(-2.0, log_ma50))
            
            if abs(ma200_dist) > 0.1:
                log_ma200 = math.copysign(
                    math.log1p(abs(ma200_dist)) * 0.3,  # Lower weight for MA200
                    ma200_dist
                )
                ma_score += min(0.8, max(-0.8, log_ma200))
            
            ma_score = min(2.5, max(-2.5, ma_score))
            
            # ================================================================
            # 5. TANH NORMALIZATION → [-10, +10]
            # ================================================================
            # Sum all raw components
            total_raw = momentum_force + rsi_score + bb_score + ma_score
            
            # Scaling factor k: controls sensitivity
            # k=0.15 means raw_score of ±7 maps to about ±7.5 final
            # k=0.20 means faster saturation (hits ±9 sooner)
            k = 0.18
            
            final_score = 10.0 * math.tanh(k * total_raw)
            
            # ================================================================
            # 6. CONFIDENCE LEVEL (ATR-based, 0-100%)
            # ================================================================
            # Base confidence from ATR (noise level)
            if atr_pct > 4.0:
                # Extreme volatility → low confidence
                base_confidence = 30.0
            elif atr_pct > 3.0:
                # High volatility
                base_confidence = 50.0
            elif atr_pct > 1.5:
                # Moderate volatility → decent confidence
                base_confidence = 70.0
            else:
                # Low volatility
                base_confidence = 80.0
            
            # Squeeze boost: low ATR + narrow Bollinger = breakout imminent
            if atr_pct < 1.5 and bb_width < 5.0:
                base_confidence += 15.0  # High confidence in pending breakout
            
            # Signal alignment boost: momentum agrees with Bollinger position
            if (momentum > 0 and bb_pctb > 0.5) or (momentum < 0 and bb_pctb < 0.5):
                base_confidence += 5.0
            
            # Volume confirmation boost
            if volume_ratio > 1.5:
                base_confidence += 5.0
            elif volume_ratio < 0.5:
                base_confidence -= 10.0  # Low volume = unreliable signal
            
            confidence_level = min(100.0, max(10.0, base_confidence))
            
            # ================================================================
            # BUILD RESULT
            # ================================================================
            breakdown = {
                'momentum_force': round(momentum_force, 3),
                'rsi_penalty': round(rsi_score, 3),
                'bollinger_signal': round(bb_score, 3),
                'ma_convergence': round(ma_score, 3),
                'total_raw': round(total_raw, 3),
                'vol_multiplier': round(vol_multiplier, 3),
                'k_factor': k,
            }
            
            logger.debug(
                f"Physics Score: Mom_Force={momentum_force:+.2f} (mom={momentum:+.1f}% × vol={vol_multiplier:.2f}), "
                f"RSI={rsi_score:+.2f}, BB={bb_score:+.2f}, MA={ma_score:+.2f} "
                f"→ Raw={total_raw:+.2f} → tanh → Final={final_score:+.2f} (Conf={confidence_level:.0f}%)"
            )
            
            return {
                'technical_score': final_score,
                'confidence_level': confidence_level,
                'contribution_breakdown': breakdown
            }
            
        except Exception as e:
            logger.warning(f"Error calculating technical score: {str(e)}")
            return {
                'technical_score': 0.0,
                'confidence_level': 50.0,
                'contribution_breakdown': {}
            }


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
