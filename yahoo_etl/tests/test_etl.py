import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from etl import YahooETL
import os

class TestYahooETL:
    @pytest.fixture
    def etl(self):
        """Create ETL instance for testing"""
        return YahooETL("sqlite:///./test.db")
    
    @pytest.fixture
    def sample_price_data(self):
        """Create sample price data for testing"""
        now = datetime.utcnow()
        data = {
            'Datetime': [now - timedelta(minutes=5), now - timedelta(minutes=4)],
            'Open': [150.00, 150.50],
            'High': [151.00, 152.00],
            'Low': [149.50, 150.00],
            'Close': [150.50, 151.50],
            'Volume': [1000000, 1200000]
        }
        return pd.DataFrame(data)
    
    @pytest.fixture
    def sample_processed_data(self):
        """Create sample processed data for testing"""
        now = datetime.utcnow()
        data = {
            'symbol': ['AAPL', 'AAPL'],
            'ts': [now - timedelta(minutes=5), now - timedelta(minutes=4)],
            'o': [150.00, 150.50],
            'h': [151.00, 152.00],
            'l': [149.50, 150.00],
            'c': [150.50, 151.50],
            'v': [1000000, 1200000]
        }
        return pd.DataFrame(data)

    @patch('yfinance.Ticker')
    def test_fetch_data_success(self, mock_ticker, etl, sample_price_data):
        """Test successful data fetching"""
        # Mock the ticker and its history method
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = sample_price_data
        mock_ticker.return_value = mock_ticker_instance
        
        result = etl.fetch_data("AAPL")
        
        assert not result.empty
        assert "symbol" in result.columns
        assert "ts" in result.columns
        assert "o" in result.columns
        assert "h" in result.columns
        assert "l" in result.columns
        assert "c" in result.columns
        assert "v" in result.columns
        assert result["symbol"].iloc[0] == "AAPL"
        
        # Verify yfinance was called correctly
        mock_ticker.assert_called_once_with("AAPL")
        mock_ticker_instance.history.assert_called_once_with(period="1d", interval="1m")

    @patch('yfinance.Ticker')
    def test_fetch_data_empty(self, mock_ticker, etl):
        """Test data fetching when no data is available"""
        # Mock empty data
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_ticker_instance
        
        result = etl.fetch_data("INVALID")
        
        assert result.empty

    @patch('yfinance.Ticker')
    def test_fetch_data_exception(self, mock_ticker, etl):
        """Test data fetching when exception occurs"""
        # Mock exception
        mock_ticker.side_effect = Exception("Network error")
        
        result = etl.fetch_data("AAPL")
        
        assert result.empty

    def test_calculate_indicators_ema(self, etl, sample_processed_data):
        """Test EMA calculation"""
        result = etl.calculate_indicators("AAPL", sample_processed_data)
        
        assert not result.empty
        assert "indicator_type" in result.columns
        assert "value" in result.columns
        assert "period" in result.columns
        
        # Check for EMA indicators
        ema_indicators = result[result["indicator_type"] == "ema"]
        assert not ema_indicators.empty
        assert set(ema_indicators["period"].unique()) == {9, 21, 50}

    def test_calculate_indicators_rsi(self, etl, sample_processed_data):
        """Test RSI calculation"""
        # Create more data points for RSI calculation
        now = datetime.utcnow()
        extended_data = []
        for i in range(20):
            extended_data.append({
                'symbol': 'AAPL',
                'ts': now - timedelta(minutes=20-i),
                'o': 150.0 + i * 0.1,
                'h': 151.0 + i * 0.1,
                'l': 149.0 + i * 0.1,
                'c': 150.0 + i * 0.1,
                'v': 1000000
            })
        
        extended_df = pd.DataFrame(extended_data)
        result = etl.calculate_indicators("AAPL", extended_df)
        
        # Check for RSI indicators
        rsi_indicators = result[result["indicator_type"] == "rsi"]
        assert not rsi_indicators.empty
        assert all(rsi_indicators["period"] == 14)

    def test_calculate_indicators_insufficient_data(self, etl):
        """Test indicator calculation with insufficient data"""
        # Create minimal data
        now = datetime.utcnow()
        minimal_data = pd.DataFrame({
            'symbol': ['AAPL'],
            'ts': [now],
            'o': [150.0],
            'h': [151.0],
            'l': [149.0],
            'c': [150.0],
            'v': [1000000]
        })
        
        result = etl.calculate_indicators("AAPL", minimal_data)
        
        assert result.empty

    def test_calculate_rsi_method(self, etl):
        """Test RSI calculation method directly"""
        # Create sample price series
        prices = pd.Series([100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 111, 110, 112, 114, 113, 115])
        
        rsi = etl._calculate_rsi(prices, 14)
        
        assert len(rsi) == len(prices)
        assert not rsi.isna().all()  # Should have some valid RSI values
        assert all(0 <= val <= 100 for val in rsi.dropna())  # RSI should be between 0 and 100

    @patch('etl.YahooETL.Session')
    def test_upsert_prices_success(self, mock_session, etl, sample_processed_data):
        """Test successful price upsert"""
        # Mock database session
        mock_db = Mock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_session.return_value.__exit__.return_value = None
        
        result = etl.upsert_prices(sample_processed_data)
        
        assert result == len(sample_processed_data)
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('etl.YahooETL.Session')
    def test_upsert_prices_exception(self, mock_session, etl, sample_processed_data):
        """Test price upsert with exception"""
        # Mock database session with exception
        mock_db = Mock()
        mock_db.execute.side_effect = Exception("Database error")
        mock_session.return_value.__enter__.return_value = mock_db
        mock_session.return_value.__exit__.return_value = None
        
        result = etl.upsert_prices(sample_processed_data)
        
        assert result == 0

    def test_upsert_prices_empty_data(self, etl):
        """Test price upsert with empty data"""
        empty_df = pd.DataFrame()
        result = etl.upsert_prices(empty_df)
        
        assert result == 0

    @patch('etl.YahooETL.Session')
    def test_upsert_indicators_success(self, mock_session, etl):
        """Test successful indicator upsert"""
        # Create sample indicator data
        now = datetime.utcnow()
        indicator_data = pd.DataFrame({
            'symbol': ['AAPL', 'AAPL'],
            'ts': [now, now - timedelta(minutes=1)],
            'indicator_type': ['ema', 'rsi'],
            'value': [150.25, 65.5],
            'period': [21, 14]
        })
        
        # Mock database session
        mock_db = Mock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_session.return_value.__exit__.return_value = None
        
        result = etl.upsert_indicators(indicator_data)
        
        assert result == len(indicator_data)
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('etl.YahooETL.Session')
    def test_upsert_indicators_exception(self, mock_session, etl):
        """Test indicator upsert with exception"""
        # Create sample indicator data
        now = datetime.utcnow()
        indicator_data = pd.DataFrame({
            'symbol': ['AAPL'],
            'ts': [now],
            'indicator_type': ['ema'],
            'value': [150.25],
            'period': [21]
        })
        
        # Mock database session with exception
        mock_db = Mock()
        mock_db.execute.side_effect = Exception("Database error")
        mock_session.return_value.__enter__.return_value = mock_db
        mock_session.return_value.__exit__.return_value = None
        
        result = etl.upsert_indicators(indicator_data)
        
        assert result == 0

    @patch('etl.YahooETL.fetch_data')
    @patch('etl.YahooETL.upsert_prices')
    @patch('etl.YahooETL.calculate_indicators')
    @patch('etl.YahooETL.upsert_indicators')
    def test_process_symbol_success(self, mock_upsert_indicators, mock_calculate_indicators, 
                                   mock_upsert_prices, mock_fetch_data, etl, sample_processed_data):
        """Test successful symbol processing"""
        # Mock all methods
        mock_fetch_data.return_value = sample_processed_data
        mock_upsert_prices.return_value = len(sample_processed_data)
        mock_calculate_indicators.return_value = pd.DataFrame({
            'symbol': ['AAPL'],
            'ts': [datetime.utcnow()],
            'indicator_type': ['ema'],
            'value': [150.25],
            'period': [21]
        })
        mock_upsert_indicators.return_value = 1
        
        result = etl.process_symbol("AAPL")
        
        assert result["prices"] == len(sample_processed_data)
        assert result["indicators"] == 1
        mock_fetch_data.assert_called_once_with("AAPL", "1d", "1m")
        mock_upsert_prices.assert_called_once()
        mock_calculate_indicators.assert_called_once()
        mock_upsert_indicators.assert_called_once()

    @patch('etl.YahooETL.fetch_data')
    def test_process_symbol_empty_data(self, mock_fetch_data, etl):
        """Test symbol processing with empty data"""
        mock_fetch_data.return_value = pd.DataFrame()
        
        result = etl.process_symbol("INVALID")
        
        assert result["prices"] == 0
        assert result["indicators"] == 0

    @patch('etl.YahooETL.process_symbol')
    def test_process_all_symbols_success(self, mock_process_symbol, etl):
        """Test processing all symbols successfully"""
        # Mock process_symbol to return success
        mock_process_symbol.return_value = {"prices": 10, "indicators": 5}
        
        result = etl.process_all_symbols()
        
        assert result["total_symbols"] == len(etl.symbols)
        assert result["successful"] == len(etl.symbols)
        assert result["failed"] == 0
        assert result["total_prices"] == len(etl.symbols) * 10
        assert result["total_indicators"] == len(etl.symbols) * 5

    @patch('etl.YahooETL.process_symbol')
    def test_process_all_symbols_with_failures(self, mock_process_symbol, etl):
        """Test processing all symbols with some failures"""
        # Mock process_symbol to raise exception for some symbols
        def side_effect(symbol):
            if symbol == "INVALID":
                raise Exception("Symbol not found")
            return {"prices": 10, "indicators": 5}
        
        mock_process_symbol.side_effect = side_effect
        etl.symbols = ["AAPL", "MSFT", "INVALID"]  # Override symbols for testing
        
        result = etl.process_all_symbols()
        
        assert result["total_symbols"] == 3
        assert result["successful"] == 2
        assert result["failed"] == 1
        assert "INVALID" in result["symbols"]
        assert "error" in result["symbols"]["INVALID"]
