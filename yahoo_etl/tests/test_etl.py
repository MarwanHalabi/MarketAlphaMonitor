from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from contextlib import ExitStack
from unittest import TestCase, skipIf
from unittest.mock import Mock, patch

try:
    import pandas as pd
except ModuleNotFoundError:  # pragma: no cover - handled during tests
    pd = None

if pd is not None:
    from yahoo_etl.etl import YahooETL
else:  # pragma: no cover - executed when pandas is unavailable.
    YahooETL = None


@skipIf(YahooETL is None, "pandas is required for YahooETL tests")
class YahooETLTestCase(TestCase):
    database_url = "sqlite:///./yahoo_etl_test.db"

    @classmethod
    def tearDownClass(cls) -> None:
        db_path = Path(cls.database_url.replace("sqlite:///", ""))
        if db_path.exists():
            db_path.unlink()
        super().tearDownClass()

    def setUp(self) -> None:
        db_path = Path(self.database_url.replace("sqlite:///", ""))
        if db_path.exists():
            db_path.unlink()
        self.etl = YahooETL(self.database_url)
        self.etl.symbols = ["AAPL", "MSFT"]

    def tearDown(self) -> None:
        self.etl.engine.dispose()
        super().tearDown()

    @staticmethod
    def yahoo_history_frame() -> pd.DataFrame:
        now = datetime.now(timezone.utc)
        return pd.DataFrame(
            {
                "Datetime": [now - timedelta(minutes=5), now - timedelta(minutes=4)],
                "Open": [150.0, 150.5],
                "High": [151.0, 152.0],
                "Low": [149.5, 150.0],
                "Close": [150.5, 151.5],
                "Volume": [1_000_000, 1_200_000],
            }
        )

    @staticmethod
    def processed_price_frame(rows: int = 2) -> pd.DataFrame:
        now = datetime.now(timezone.utc)
        data = []
        for idx in range(rows):
            data.append(
                {
                    "symbol": "AAPL",
                    "ts": now - timedelta(minutes=rows - idx),
                    "o": 150.0 + idx * 0.5,
                    "h": 151.0 + idx * 0.5,
                    "l": 149.5 + idx * 0.5,
                    "c": 150.5 + idx * 0.5,
                    "v": 1_000_000 + idx * 100_000,
                }
            )
        return pd.DataFrame(data)

    def test_fetch_data_success(self) -> None:
        with patch("yahoo_etl.etl.yf.Ticker") as mock_ticker:
            ticker_instance = Mock()
            ticker_instance.history.return_value = self.yahoo_history_frame()
            mock_ticker.return_value = ticker_instance

            result = self.etl.fetch_data("AAPL")

            self.assertFalse(result.empty)
            self.assertTrue({"symbol", "ts", "o", "h", "l", "c", "v"}.issubset(result.columns))
            self.assertEqual(result["symbol"].iloc[0], "AAPL")
            mock_ticker.assert_called_once_with("AAPL")
            ticker_instance.history.assert_called_once_with(period="1d", interval="1m")

    def test_fetch_data_empty(self) -> None:
        with patch("yahoo_etl.etl.yf.Ticker") as mock_ticker:
            ticker_instance = Mock()
            ticker_instance.history.return_value = pd.DataFrame()
            mock_ticker.return_value = ticker_instance

            result = self.etl.fetch_data("INVALID")
            self.assertTrue(result.empty)

    def test_fetch_data_exception(self) -> None:
        with patch("yahoo_etl.etl.yf.Ticker", side_effect=Exception("Network error")):
            result = self.etl.fetch_data("AAPL")
            self.assertTrue(result.empty)

    def test_calculate_indicators_ema(self) -> None:
        data = self.processed_price_frame(rows=60)
        result = self.etl.calculate_indicators("AAPL", data)
        ema = result[result["indicator_type"] == "ema"]
        self.assertFalse(ema.empty)
        self.assertTrue(set(ema["period"].unique()).issuperset({9, 21, 50}))

    def test_calculate_indicators_rsi(self) -> None:
        rows = []
        now = datetime.now(timezone.utc)
        for index in range(20):
            rows.append(
                {
                    "symbol": "AAPL",
                    "ts": now - timedelta(minutes=20 - index),
                    "o": 150.0 + index,
                    "h": 151.0 + index,
                    "l": 149.0 + index,
                    "c": 150.0 + index,
                    "v": 1_000_000,
                }
            )
        data = pd.DataFrame(rows)
        result = self.etl.calculate_indicators("AAPL", data)
        rsi = result[result["indicator_type"] == "rsi"]
        self.assertFalse(rsi.empty)
        self.assertTrue((rsi["period"] == 14).all())

    def test_calculate_indicators_insufficient_data(self) -> None:
        data = self.processed_price_frame(rows=1)
        result = self.etl.calculate_indicators("AAPL", data)
        self.assertTrue(result.empty)

    def test_calculate_rsi_method(self) -> None:
        series = pd.Series([100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 111, 110, 112, 114, 113, 115])
        rsi = self.etl._calculate_rsi(series, 14)
        self.assertEqual(len(rsi), len(series))
        self.assertFalse(rsi.isna().all())
        self.assertTrue(((rsi.dropna() >= 0) & (rsi.dropna() <= 100)).all())

    def test_upsert_prices_success(self) -> None:
        with patch("yahoo_etl.etl.YahooETL.Session") as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_session.return_value.__exit__.return_value = None

            count = self.etl.upsert_prices(self.processed_price_frame())
            self.assertEqual(count, 2)
            mock_db.execute.assert_called_once()
            mock_db.commit.assert_called_once()

    def test_upsert_prices_exception(self) -> None:
        with patch("yahoo_etl.etl.YahooETL.Session") as mock_session:
            mock_db = Mock()
            mock_db.execute.side_effect = Exception("Database error")
            mock_session.return_value.__enter__.return_value = mock_db
            mock_session.return_value.__exit__.return_value = None

            count = self.etl.upsert_prices(self.processed_price_frame())
            self.assertEqual(count, 0)

    def test_upsert_prices_empty_data(self) -> None:
        self.assertEqual(self.etl.upsert_prices(pd.DataFrame()), 0)

    def test_upsert_indicators_success(self) -> None:
        with patch("yahoo_etl.etl.YahooETL.Session") as mock_session:
            mock_db = Mock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_session.return_value.__exit__.return_value = None

            now = datetime.now(timezone.utc)
            indicators = pd.DataFrame(
                {
                    "symbol": ["AAPL", "AAPL"],
                    "ts": [now, now - timedelta(minutes=1)],
                    "indicator_type": ["ema", "rsi"],
                    "value": [150.25, 65.5],
                    "period": [21, 14],
                }
            )

            count = self.etl.upsert_indicators(indicators)
            self.assertEqual(count, 2)
            mock_db.execute.assert_called_once()
            mock_db.commit.assert_called_once()

    def test_upsert_indicators_exception(self) -> None:
        with patch("yahoo_etl.etl.YahooETL.Session") as mock_session:
            mock_db = Mock()
            mock_db.execute.side_effect = Exception("Database error")
            mock_session.return_value.__enter__.return_value = mock_db
            mock_session.return_value.__exit__.return_value = None

            now = datetime.now(timezone.utc)
            indicators = pd.DataFrame(
                {
                    "symbol": ["AAPL"],
                    "ts": [now],
                    "indicator_type": ["ema"],
                    "value": [150.25],
                    "period": [21],
                }
            )

            self.assertEqual(self.etl.upsert_indicators(indicators), 0)

    def test_process_symbol_success(self) -> None:
        with ExitStack() as stack:
            mock_fetch = stack.enter_context(
                patch("yahoo_etl.etl.YahooETL.fetch_data", return_value=self.processed_price_frame())
            )
            mock_upsert_prices = stack.enter_context(
                patch("yahoo_etl.etl.YahooETL.upsert_prices", return_value=2)
            )
            mock_calculate = stack.enter_context(
                patch(
                    "yahoo_etl.etl.YahooETL.calculate_indicators",
                    return_value=pd.DataFrame(
                        {
                            "symbol": ["AAPL"],
                            "ts": [datetime.now(timezone.utc)],
                            "indicator_type": ["ema"],
                            "value": [150.25],
                            "period": [21],
                        }
                    ),
                )
            )
            mock_upsert_indicators = stack.enter_context(
                patch("yahoo_etl.etl.YahooETL.upsert_indicators", return_value=1)
            )

            result = self.etl.process_symbol("AAPL")
            self.assertEqual(result, {"prices": 2, "indicators": 1})
            mock_fetch.assert_called_once_with("AAPL", "1d", "1m")
            mock_upsert_prices.assert_called_once()
            mock_calculate.assert_called_once()
            mock_upsert_indicators.assert_called_once()

    def test_process_symbol_empty_data(self) -> None:
        with patch("yahoo_etl.etl.YahooETL.fetch_data", return_value=pd.DataFrame()):
            result = self.etl.process_symbol("INVALID")
            self.assertEqual(result, {"prices": 0, "indicators": 0})

    @patch("yahoo_etl.etl.time.sleep", return_value=None)
    def test_process_all_symbols_success(self, _mock_sleep) -> None:
        with patch("yahoo_etl.etl.YahooETL.process_symbol", return_value={"prices": 10, "indicators": 5}):
            result = self.etl.process_all_symbols()
            self.assertEqual(result["total_symbols"], len(self.etl.symbols))
            self.assertEqual(result["successful"], len(self.etl.symbols))
            self.assertEqual(result["failed"], 0)
            self.assertEqual(result["total_prices"], len(self.etl.symbols) * 10)
            self.assertEqual(result["total_indicators"], len(self.etl.symbols) * 5)

    @patch("yahoo_etl.etl.time.sleep", return_value=None)
    def test_process_all_symbols_with_failures(self, _mock_sleep) -> None:
        def side_effect(symbol: str):
            if symbol == "INVALID":
                raise Exception("Symbol not found")
            return {"prices": 10, "indicators": 5}

        with patch("yahoo_etl.etl.YahooETL.process_symbol", side_effect=side_effect):
            self.etl.symbols = ["AAPL", "MSFT", "INVALID"]
            result = self.etl.process_all_symbols()
            self.assertEqual(result["total_symbols"], 3)
            self.assertEqual(result["successful"], 2)
            self.assertEqual(result["failed"], 1)
            self.assertIn("INVALID", result["symbols"])
            self.assertIn("error", result["symbols"]["INVALID"])
