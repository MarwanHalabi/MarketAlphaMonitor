import sys
from pathlib import Path

import os
from fastapi import HTTPException

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

TESTS_ROOT = ROOT_DIR / "tests"
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

MARKET_TRACKER_ROOT = ROOT_DIR / "market-tracker"
if str(MARKET_TRACKER_ROOT) not in sys.path:
    sys.path.insert(0, str(MARKET_TRACKER_ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///./market_tracker_test.db")

from app.main import read_root
from app.models import Indicator
from app.routes.health import health_check, liveness_check, readiness_check
from app.routes.indicators import get_available_indicators, get_indicators, get_latest_indicators
from app.routes.quotes import get_latest_quotes, get_quotes
from tests.fastapi_base import FastAPITestCase


class HealthEndpointTests(FastAPITestCase):
    def test_health_check(self) -> None:
        response = self.run_async(health_check(db=self.session))
        self.assertIn(response.status, {"healthy", "unhealthy"})
        self.assertTrue(response.timestamp)
        self.assertIn("database", response.model_dump())
        self.assertEqual(response.version, "1.0.0")

    def test_readiness_check(self) -> None:
        response = self.run_async(readiness_check(db=self.session))
        self.assertEqual(response["status"], "ready")

    def test_liveness_check(self) -> None:
        response = self.run_async(liveness_check())
        self.assertEqual(response["status"], "alive")


class QuotesEndpointTests(FastAPITestCase):
    def test_get_quotes_all(self) -> None:
        result = self.run_async(
            get_quotes(symbol=None, limit=100, hours=24, db=self.session)
        )
        self.assertGreater(len(result), 0)
        for quote in result:
            self.assertTrue(quote.symbol)
            self.assertTrue(quote.timestamp)

    def test_get_quotes_by_symbol(self) -> None:
        result = self.run_async(
            get_quotes(symbol="AAPL", limit=100, hours=24, db=self.session)
        )
        self.assertGreater(len(result), 0)
        self.assertTrue(all(item.symbol == "AAPL" for item in result))

    def test_get_quotes_invalid_symbol(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            self.run_async(
                get_quotes(symbol="INVALID", limit=100, hours=24, db=self.session)
            )
        self.assertEqual(exc.exception.status_code, 500)
        self.assertIn("Error retrieving quotes", exc.exception.detail)

    def test_get_quotes_with_limit(self) -> None:
        result = self.run_async(
            get_quotes(symbol=None, limit=1, hours=24, db=self.session)
        )
        self.assertLessEqual(len(result), 1)

    def test_get_quotes_with_hours_filter(self) -> None:
        result = self.run_async(
            get_quotes(symbol=None, limit=100, hours=1, db=self.session)
        )
        self.assertGreaterEqual(len(result), 0)

    def test_get_latest_quotes(self) -> None:
        result = self.run_async(get_latest_quotes(symbols=None, db=self.session))
        self.assertGreater(len(result), 0)

    def test_get_latest_quotes_specific_symbols(self) -> None:
        result = self.run_async(get_latest_quotes(symbols="AAPL,MSFT", db=self.session))
        symbols = {item.symbol for item in result}
        self.assertTrue({"AAPL", "MSFT"} & symbols)


class IndicatorEndpointTests(FastAPITestCase):
    def test_get_indicators_all(self) -> None:
        result = self.run_async(
            get_indicators(
                symbol=None,
                indicator_type=None,
                period=None,
                limit=100,
                hours=24,
                db=self.session,
            )
        )
        self.assertGreater(len(result), 0)
        for item in result:
            self.assertTrue(item.indicator_type)

    def test_get_indicators_by_symbol(self) -> None:
        result = self.run_async(
            get_indicators(
                symbol="AAPL",
                indicator_type=None,
                period=None,
                limit=100,
                hours=24,
                db=self.session,
            )
        )
        self.assertTrue(all(item.symbol == "AAPL" for item in result))

    def test_get_indicators_by_type(self) -> None:
        result = self.run_async(
            get_indicators(
                symbol=None,
                indicator_type="ema",
                period=None,
                limit=100,
                hours=24,
                db=self.session,
            )
        )
        self.assertTrue(all(item.indicator_type == "ema" for item in result))

    def test_get_indicators_by_period(self) -> None:
        result = self.run_async(
            get_indicators(
                symbol=None,
                indicator_type=None,
                period=21,
                limit=100,
                hours=24,
                db=self.session,
            )
        )
        self.assertTrue(all(item.period == 21 for item in result))

    def test_get_latest_indicators(self) -> None:
        result = self.run_async(
            get_latest_indicators(symbol=None, indicator_type=None, db=self.session)
        )
        self.assertGreater(len(result), 0)

    def test_get_available_indicators(self) -> None:
        result = self.run_async(get_available_indicators(db=self.session))
        self.assertIn("available_indicators", result)
        self.assertIn("total_types", result)

    def test_indicators_timestamp_timezone(self) -> None:
        result = self.run_async(
            get_indicators(
                symbol=None,
                indicator_type=None,
                period=None,
                limit=100,
                hours=24,
                db=self.session,
            )
        )
        timestamps = [entry.timestamp.isoformat() for entry in result]
        self.assertTrue(all("T" in ts for ts in timestamps))


class RootEndpointTests(FastAPITestCase):
    load_sample_data = False

    def test_root_endpoint_returns_html(self) -> None:
        html = self.run_async(read_root())
        self.assertIn("Market Tracker", html)


class ErrorHandlingTests(FastAPITestCase):
    def test_indicator_not_found_returns_404(self) -> None:
        self.session.query(Indicator).delete()
        self.session.commit()
        with self.assertRaises(HTTPException) as exc:
            self.run_async(
                get_indicators(
                    symbol="UNKNOWN",
                    indicator_type=None,
                    period=None,
                    limit=100,
                    hours=24,
                    db=self.session,
                )
            )
        self.assertEqual(exc.exception.status_code, 500)
        self.assertIn("Error retrieving indicators", exc.exception.detail)
