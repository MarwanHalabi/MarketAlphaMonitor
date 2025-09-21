import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime, timedelta
import logging
import time
from typing import List, Dict, Any
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YahooETL:
    Session = None  # type: ignore[assignment]

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        session_factory = sessionmaker(bind=self.engine)
        # Store the factory on the class so tests can patch YahooETL.Session.
        self.__class__.Session = session_factory
        
        # Default symbols to track
        self.symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX"]
        
    def fetch_data(self, symbol: str, period: str = "1d", interval: str = "1m") -> pd.DataFrame:
        """
        Fetch market data from Yahoo Finance for a given symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            period: Data period ('1d', '5d', '1mo', etc.)
            interval: Data interval ('1m', '5m', '15m', '1h', '1d')
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                logger.warning(f"No data found for symbol: {symbol}")
                return pd.DataFrame()
            
            # Reset index to make timestamp a column
            data = data.reset_index()
            
            # Rename columns to match database schema
            data = data.rename(columns={
                'Datetime': 'ts',
                'Open': 'o',
                'High': 'h',
                'Low': 'l',
                'Close': 'c',
                'Volume': 'v'
            })
            
            # Add symbol column
            data['symbol'] = symbol.upper()
            
            # Ensure timestamp is timezone aware (fix timezone issue)
            if 'ts' in data.columns:
                if data['ts'].dt.tz is None:
                    data['ts'] = pd.to_datetime(data['ts']).dt.tz_localize('UTC')
                else:
                    data['ts'] = pd.to_datetime(data['ts']).dt.tz_convert('UTC')
            
            # Select only required columns
            columns = ['symbol', 'ts', 'o', 'h', 'l', 'c', 'v']
            data = data[columns]
            
            logger.info(f"Fetched {len(data)} records for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def upsert_prices(self, data: pd.DataFrame) -> int:
        """
        Upsert price data into the database.
        
        Args:
            data: DataFrame with price data
        
        Returns:
            Number of records processed
        """
        if data.empty:
            return 0
        
        try:
            with self.Session() as session:
                # Convert DataFrame to list of dictionaries
                records = data.to_dict('records')
                
                # Use raw SQL with proper table reference
                stmt = text("""
                    INSERT INTO prices (symbol, ts, o, h, l, c, v)
                    VALUES (:symbol, :ts, :o, :h, :l, :c, :v)
                    ON CONFLICT (symbol, ts) 
                    DO UPDATE SET
                        o = EXCLUDED.o,
                        h = EXCLUDED.h,
                        l = EXCLUDED.l,
                        c = EXCLUDED.c,
                        v = EXCLUDED.v
                """)
                
                session.execute(stmt, records)
                session.commit()
                
                logger.info(f"Upserted {len(records)} price records")
                return len(records)
                
        except Exception as e:
            logger.error(f"Error upserting prices: {str(e)}")
            return 0
    
    def calculate_indicators(self, symbol: str, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for the given data.
        
        Args:
            symbol: Stock symbol
            data: DataFrame with price data
        
        Returns:
            DataFrame with calculated indicators
        """
        if data.empty or len(data) < 20:  # Need at least 20 data points for indicators
            return pd.DataFrame()
        
        try:
            indicators = []
            
            # Calculate EMA (Exponential Moving Average) for different periods
            for period in [9, 21, 50]:
                if len(data) >= period:
                    ema = data['c'].ewm(span=period).mean()
                    for i, (ts, value) in enumerate(zip(data['ts'], ema)):
                        indicators.append({
                            'symbol': symbol.upper(),
                            'ts': ts,
                            'indicator_type': 'ema',
                            'value': float(value),
                            'period': period
                        })
            
            # Calculate RSI (Relative Strength Index)
            if len(data) >= 14:
                rsi = self._calculate_rsi(data['c'], 14)
                for ts, value in zip(data['ts'], rsi):
                    if not pd.isna(value):
                        indicators.append({
                            'symbol': symbol.upper(),
                            'ts': ts,
                            'indicator_type': 'rsi',
                            'value': float(value),
                            'period': 14
                        })
            
            return pd.DataFrame(indicators)
            
        except Exception as e:
            logger.error(f"Error calculating indicators for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def upsert_indicators(self, data: pd.DataFrame) -> int:
        """
        Upsert indicator data into the database.
        
        Args:
            data: DataFrame with indicator data
        
        Returns:
            Number of records processed
        """
        if data.empty:
            return 0
        
        try:
            with self.Session() as session:
                records = data.to_dict('records')
                
                stmt = text("""
                    INSERT INTO indicators (symbol, ts, indicator_type, value, period)
                    VALUES (:symbol, :ts, :indicator_type, :value, :period)
                    ON CONFLICT (symbol, ts, indicator_type, period) 
                    DO UPDATE SET
                        value = EXCLUDED.value
                """)
                
                session.execute(stmt, records)
                session.commit()
                
                logger.info(f"Upserted {len(records)} indicator records")
                return len(records)
                
        except Exception as e:
            logger.error(f"Error upserting indicators: {str(e)}")
            return 0
    
    def process_symbol(self, symbol: str) -> Dict[str, int]:
        """
        Process a single symbol: fetch data, upsert prices, calculate and upsert indicators.
        
        Args:
            symbol: Stock symbol to process
        
        Returns:
            Dictionary with processing results
        """
        logger.info(f"Processing symbol: {symbol}")
        
        # Fetch data
        data = self.fetch_data(symbol, "1d", "1m")
        
        if data.empty:
            return {"prices": 0, "indicators": 0}
        
        # Upsert prices
        prices_count = self.upsert_prices(data)
        
        # Calculate and upsert indicators
        indicators_data = self.calculate_indicators(symbol, data)
        indicators_count = self.upsert_indicators(indicators_data)
        
        return {
            "prices": prices_count,
            "indicators": indicators_count
        }
    
    def process_all_symbols(self) -> Dict[str, Any]:
        """
        Process all configured symbols.
        
        Returns:
            Dictionary with overall processing results
        """
        logger.info(f"Processing {len(self.symbols)} symbols")
        
        results = {
            "total_symbols": len(self.symbols),
            "successful": 0,
            "failed": 0,
            "total_prices": 0,
            "total_indicators": 0,
            "symbols": {}
        }
        
        for symbol in self.symbols:
            try:
                symbol_result = self.process_symbol(symbol)
                results["symbols"][symbol] = symbol_result
                results["successful"] += 1
                results["total_prices"] += symbol_result["prices"]
                results["total_indicators"] += symbol_result["indicators"]
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to process {symbol}: {str(e)}")
                results["symbols"][symbol] = {"error": str(e)}
                results["failed"] += 1
        
        logger.info(f"Processing complete: {results['successful']} successful, {results['failed']} failed")
        return results

def main():
    """Main function for running ETL process"""
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/market_tracker")
    
    etl = YahooETL(database_url)
    results = etl.process_all_symbols()
    
    print(f"ETL Process Complete:")
    print(f"  Total symbols: {results['total_symbols']}")
    print(f"  Successful: {results['successful']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Total prices: {results['total_prices']}")
    print(f"  Total indicators: {results['total_indicators']}")

if __name__ == "__main__":
    main()
