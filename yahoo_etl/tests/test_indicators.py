from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import TestCase, skipIf

try:
    import pandas as pd
except ModuleNotFoundError:  # pragma: no cover
    pd = None

if pd is not None:
    from yahoo_etl.etl import YahooETL
else:  # pragma: no cover
    YahooETL = None


@skipIf(YahooETL is None, "pandas is required for YahooETL tests")
class IndicatorCalculationTests(TestCase):
    database_url = "sqlite:///./yahoo_etl_indicator_test.db"

    @classmethod
    def tearDownClass(cls) -> None:
        db_path = cls.database_url.replace("sqlite:///", "")
        path = Path(db_path)
        if path.exists():
            path.unlink()
        super().tearDownClass()

    def setUp(self) -> None:
        path = Path(self.database_url.replace("sqlite:///", ""))
        if path.exists():
            path.unlink()
        self.etl = YahooETL(self.database_url)

    def tearDown(self) -> None:
        self.etl.engine.dispose()
        super().tearDown()

    @staticmethod
    def make_price_data(count: int = 50, start: float = 150.0, step: float = 0.5) -> pd.DataFrame:
        now = datetime.now(timezone.utc)
        rows = []
        for index in range(count):
            price = start + index * step
            rows.append(
                {
                    "symbol": "AAPL",
                    "ts": now - timedelta(minutes=count - index),
                    "o": price - 0.1,
                    "h": price + 0.2,
                    "l": price - 0.2,
                    "c": price,
                    "v": 1_000_000 + index * 1_000,
                }
            )
        return pd.DataFrame(rows)

    def test_ema_calculation_for_multiple_periods(self) -> None:
        data = self.make_price_data()
        indicators = self.etl.calculate_indicators("AAPL", data)
        ema = indicators[indicators["indicator_type"] == "ema"]
        self.assertFalse(ema.empty)
        for period in (9, 21, 50):
            period_slice = ema[ema["period"] == period]
            self.assertEqual(len(period_slice), len(data))
            self.assertTrue(period_slice["value"].notna().all())

    def test_rsi_calculation_produces_values_between_bounds(self) -> None:
        data = self.make_price_data()
        indicators = self.etl.calculate_indicators("AAPL", data)
        rsi = indicators[indicators["indicator_type"] == "rsi"]
        self.assertFalse(rsi.empty)
        valid = rsi["value"].dropna()
        self.assertTrue(((valid >= 0) & (valid <= 100)).all())
        self.assertGreaterEqual(len(valid), len(data) - 14)

    def test_rsi_with_constant_prices_is_neutral(self) -> None:
        now = datetime.now(timezone.utc)
        data = pd.DataFrame(
            {
                "symbol": ["AAPL"] * 20,
                "ts": [now - timedelta(minutes=20 - idx) for idx in range(20)],
                "o": [100.0] * 20,
                "h": [100.0] * 20,
                "l": [100.0] * 20,
                "c": [100.0] * 20,
                "v": [1_000_000] * 20,
            }
        )
        indicators = self.etl.calculate_indicators("AAPL", data)
        rsi = indicators[indicators["indicator_type"] == "rsi"]
        if not rsi.empty:
            valid = rsi["value"].dropna()
            if not valid.empty:
                self.assertTrue(valid.between(40, 60).all())

    def test_rsi_detects_upward_trend(self) -> None:
        data = self.make_price_data(step=1.0)
        indicators = self.etl.calculate_indicators("AAPL", data)
        rsi = indicators[indicators["indicator_type"] == "rsi"]
        if not rsi.empty:
            valid = rsi["value"].dropna()
            if not valid.empty:
                self.assertTrue((valid > 70).any())

    def test_rsi_detects_downward_trend(self) -> None:
        data = self.make_price_data(start=200.0, step=-1.0)
        indicators = self.etl.calculate_indicators("AAPL", data)
        rsi = indicators[indicators["indicator_type"] == "rsi"]
        if not rsi.empty:
            valid = rsi["value"].dropna()
            if not valid.empty:
                self.assertTrue((valid < 30).any())

    def test_indicator_dataframe_structure(self) -> None:
        data = self.make_price_data()
        indicators = self.etl.calculate_indicators("AAPL", data)
        self.assertTrue({"symbol", "ts", "indicator_type", "value", "period"}.issubset(indicators.columns))
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(indicators["ts"]))
        self.assertTrue(pd.api.types.is_numeric_dtype(indicators["value"]))
        self.assertTrue(pd.api.types.is_numeric_dtype(indicators["period"]))
        self.assertTrue((indicators["symbol"] == "AAPL").all())
        self.assertIn("ema", indicators["indicator_type"].unique())
        self.assertIn("rsi", indicators["indicator_type"].unique())
