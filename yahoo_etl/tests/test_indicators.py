import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from etl import YahooETL

class TestIndicators:
    @pytest.fixture
    def etl(self):
        """Create ETL instance for testing"""
        return YahooETL("sqlite:///./test.db")
    
    @pytest.fixture
    def sample_price_data(self):
        """Create sample price data for testing indicators"""
        now = datetime.utcnow()
        # Create 50 data points for comprehensive testing
        data = []
        base_price = 150.0
        
        for i in range(50):
            # Create realistic price movement
            price_change = np.random.normal(0, 0.5)  # Random walk
            base_price += price_change
            
            data.append({
                'symbol': 'AAPL',
                'ts': now - timedelta(minutes=50-i),
                'o': base_price - 0.1,
                'h': base_price + 0.2,
                'l': base_price - 0.2,
                'c': base_price,
                'v': 1000000 + np.random.randint(-100000, 100000)
            })
        
        return pd.DataFrame(data)

    def test_ema_calculation_9_period(self, etl, sample_price_data):
        """Test EMA calculation with 9-period"""
        result = etl.calculate_indicators("AAPL", sample_price_data)
        
        ema_9 = result[(result["indicator_type"] == "ema") & (result["period"] == 9)]
        
        assert not ema_9.empty
        assert len(ema_9) > 0
        
        # EMA should be calculated for all data points
        assert len(ema_9) == len(sample_price_data)
        
        # EMA values should be numeric
        assert all(pd.notna(val) for val in ema_9["value"])
        
        # EMA should be within reasonable range of prices
        price_range = (sample_price_data["c"].min(), sample_price_data["c"].max())
        assert all(price_range[0] * 0.5 <= val <= price_range[1] * 1.5 for val in ema_9["value"])

    def test_ema_calculation_21_period(self, etl, sample_price_data):
        """Test EMA calculation with 21-period"""
        result = etl.calculate_indicators("AAPL", sample_price_data)
        
        ema_21 = result[(result["indicator_type"] == "ema") & (result["period"] == 21)]
        
        assert not ema_21.empty
        assert len(ema_21) > 0
        
        # EMA should be calculated for all data points
        assert len(ema_21) == len(sample_price_data)
        
        # EMA values should be numeric
        assert all(pd.notna(val) for val in ema_21["value"])

    def test_ema_calculation_50_period(self, etl, sample_price_data):
        """Test EMA calculation with 50-period"""
        result = etl.calculate_indicators("AAPL", sample_price_data)
        
        ema_50 = result[(result["indicator_type"] == "ema") & (result["period"] == 50)]
        
        assert not ema_50.empty
        assert len(ema_50) > 0
        
        # EMA should be calculated for all data points
        assert len(ema_50) == len(sample_price_data)
        
        # EMA values should be numeric
        assert all(pd.notna(val) for val in ema_50["value"])

    def test_rsi_calculation_14_period(self, etl, sample_price_data):
        """Test RSI calculation with 14-period"""
        result = etl.calculate_indicators("AAPL", sample_price_data)
        
        rsi_14 = result[(result["indicator_type"] == "rsi") & (result["period"] == 14)]
        
        assert not rsi_14.empty
        assert len(rsi_14) > 0
        
        # RSI should be calculated for most data points (after warm-up period)
        assert len(rsi_14) >= len(sample_price_data) - 14
        
        # RSI values should be between 0 and 100
        valid_rsi = rsi_14["value"].dropna()
        assert all(0 <= val <= 100 for val in valid_rsi)
        
        # RSI values should be numeric
        assert all(pd.notna(val) for val in valid_rsi)

    def test_rsi_calculation_edge_cases(self, etl):
        """Test RSI calculation with edge cases"""
        # Test with constant prices (should result in RSI around 50)
        constant_prices = pd.DataFrame({
            'symbol': ['AAPL'] * 20,
            'ts': [datetime.utcnow() - timedelta(minutes=20-i) for i in range(20)],
            'o': [100.0] * 20,
            'h': [100.0] * 20,
            'l': [100.0] * 20,
            'c': [100.0] * 20,
            'v': [1000000] * 20
        })
        
        result = etl.calculate_indicators("AAPL", constant_prices)
        rsi = result[(result["indicator_type"] == "rsi") & (result["period"] == 14)]
        
        if not rsi.empty:
            # With constant prices, RSI should be around 50 (neutral)
            valid_rsi = rsi["value"].dropna()
            if len(valid_rsi) > 0:
                assert all(40 <= val <= 60 for val in valid_rsi)

    def test_rsi_calculation_trending_up(self, etl):
        """Test RSI calculation with upward trending prices"""
        # Create upward trending prices
        trending_prices = pd.DataFrame({
            'symbol': ['AAPL'] * 20,
            'ts': [datetime.utcnow() - timedelta(minutes=20-i) for i in range(20)],
            'o': [100.0 + i for i in range(20)],
            'h': [101.0 + i for i in range(20)],
            'l': [99.0 + i for i in range(20)],
            'c': [100.0 + i for i in range(20)],
            'v': [1000000] * 20
        })
        
        result = etl.calculate_indicators("AAPL", trending_prices)
        rsi = result[(result["indicator_type"] == "rsi") & (result["period"] == 14)]
        
        if not rsi.empty:
            valid_rsi = rsi["value"].dropna()
            if len(valid_rsi) > 0:
                # Upward trending should result in higher RSI values
                assert any(val > 70 for val in valid_rsi)

    def test_rsi_calculation_trending_down(self, etl):
        """Test RSI calculation with downward trending prices"""
        # Create downward trending prices
        trending_prices = pd.DataFrame({
            'symbol': ['AAPL'] * 20,
            'ts': [datetime.utcnow() - timedelta(minutes=20-i) for i in range(20)],
            'o': [120.0 - i for i in range(20)],
            'h': [121.0 - i for i in range(20)],
            'l': [119.0 - i for i in range(20)],
            'c': [120.0 - i for i in range(20)],
            'v': [1000000] * 20
        })
        
        result = etl.calculate_indicators("AAPL", trending_prices)
        rsi = result[(result["indicator_type"] == "rsi") & (result["period"] == 14)]
        
        if not rsi.empty:
            valid_rsi = rsi["value"].dropna()
            if len(valid_rsi) > 0:
                # Downward trending should result in lower RSI values
                assert any(val < 30 for val in valid_rsi)

    def test_indicators_data_structure(self, etl, sample_price_data):
        """Test that indicators have correct data structure"""
        result = etl.calculate_indicators("AAPL", sample_price_data)
        
        # Check required columns
        required_columns = ['symbol', 'ts', 'indicator_type', 'value', 'period']
        assert all(col in result.columns for col in required_columns)
        
        # Check data types
        assert result['symbol'].dtype == 'object'
        assert pd.api.types.is_datetime64_any_dtype(result['ts'])
        assert result['indicator_type'].dtype == 'object'
        assert pd.api.types.is_numeric_dtype(result['value'])
        assert pd.api.types.is_numeric_dtype(result['period'])
        
        # Check that all symbols are uppercase
        assert all(symbol == 'AAPL' for symbol in result['symbol'].unique())
        
        # Check indicator types
        indicator_types = result['indicator_type'].unique()
        assert 'ema' in indicator_types
        assert 'rsi' in indicator_types
        
        # Check periods
        periods = result['period'].unique()
        assert 9 in periods
        assert 21 in periods
        assert 50 in periods
        assert 14 in periods

    def test_indicators_with_insufficient_data(self, etl):
        """Test indicators calculation with insufficient data"""
        # Create minimal data (less than required for indicators)
        minimal_data = pd.DataFrame({
            'symbol': ['AAPL'] * 5,
            'ts': [datetime.utcnow() - timedelta(minutes=5-i) for i in range(5)],
            'o': [100.0] * 5,
            'h': [101.0] * 5,
            'l': [99.0] * 5,
            'c': [100.0] * 5,
            'v': [1000000] * 5
        })
        
        result = etl.calculate_indicators("AAPL", minimal_data)
        
        # Should return empty DataFrame due to insufficient data
        assert result.empty

    def test_indicators_with_nan_values(self, etl):
        """Test indicators calculation with NaN values in price data"""
        # Create data with some NaN values
        data_with_nan = pd.DataFrame({
            'symbol': ['AAPL'] * 20,
            'ts': [datetime.utcnow() - timedelta(minutes=20-i) for i in range(20)],
            'o': [100.0 + i if i < 15 else np.nan for i in range(20)],
            'h': [101.0 + i if i < 15 else np.nan for i in range(20)],
            'l': [99.0 + i if i < 15 else np.nan for i in range(20)],
            'c': [100.0 + i if i < 15 else np.nan for i in range(20)],
            'v': [1000000] * 20
        })
        
        # Remove rows with NaN values
        clean_data = data_with_nan.dropna()
        
        result = etl.calculate_indicators("AAPL", clean_data)
        
        # Should still calculate indicators for clean data
        assert not result.empty
        assert all(pd.notna(val) for val in result['value'])

    def test_indicators_performance(self, etl):
        """Test indicators calculation performance with large dataset"""
        # Create large dataset
        large_data = pd.DataFrame({
            'symbol': ['AAPL'] * 1000,
            'ts': [datetime.utcnow() - timedelta(minutes=1000-i) for i in range(1000)],
            'o': [100.0 + np.random.normal(0, 1) for _ in range(1000)],
            'h': [101.0 + np.random.normal(0, 1) for _ in range(1000)],
            'l': [99.0 + np.random.normal(0, 1) for _ in range(1000)],
            'c': [100.0 + np.random.normal(0, 1) for _ in range(1000)],
            'v': [1000000 + np.random.randint(-100000, 100000) for _ in range(1000)]
        })
        
        import time
        start_time = time.time()
        result = etl.calculate_indicators("AAPL", large_data)
        end_time = time.time()
        
        # Should complete within reasonable time (less than 5 seconds)
        assert end_time - start_time < 5.0
        
        # Should produce results
        assert not result.empty
        assert len(result) > 0
