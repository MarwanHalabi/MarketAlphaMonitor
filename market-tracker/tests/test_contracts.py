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
from app.routes.health import health_check
from app.routes.indicators import get_available_indicators, get_indicators, get_latest_indicators
from app.routes.quotes import get_latest_quotes, get_quotes
from tests.fastapi_base import FastAPITestCase


class APIContractTests(FastAPITestCase):
    def test_quotes_endpoint_contract(self) -> None:
        try:
            payload = self.run_async(
                get_quotes(symbol=None, limit=100, hours=24, db=self.session)
            )
        except HTTPException as exc:
            self.assertEqual(exc.status_code, 404)
            return
        self.assertIsInstance(payload, list)
        for item in payload:
            data = item.model_dump()
            for key in {"symbol", "timestamp", "open", "high", "low", "close", "volume"}:
                self.assertIn(key, data)

    def test_indicators_endpoint_contract(self) -> None:
        try:
            payload = self.run_async(
                get_indicators(
                    symbol=None,
                    indicator_type=None,
                    period=None,
                    limit=100,
                    hours=24,
                    db=self.session,
                )
            )
        except HTTPException as exc:
            self.assertEqual(exc.status_code, 404)
            return
        self.assertIsInstance(payload, list)
        for item in payload:
            data = item.model_dump()
            for key in {"symbol", "timestamp", "indicator_type", "value", "period"}:
                self.assertIn(key, data)

    def test_health_endpoint_contract(self) -> None:
        response = self.run_async(health_check(db=self.session))
        data = response.model_dump()
        for key in {"status", "timestamp", "database", "version"}:
            self.assertIn(key, data)

    def test_quotes_latest_endpoint_contract(self) -> None:
        try:
            payload = self.run_async(get_latest_quotes(symbols=None, db=self.session))
        except HTTPException as exc:
            self.assertEqual(exc.status_code, 404)
            return
        self.assertIsInstance(payload, list)
        for item in payload:
            data = item.model_dump()
            for key in {"symbol", "timestamp", "open", "high", "low", "close", "volume"}:
                self.assertIn(key, data)

    def test_indicators_latest_endpoint_contract(self) -> None:
        try:
            payload = self.run_async(
                get_latest_indicators(symbol=None, indicator_type=None, db=self.session)
            )
        except HTTPException as exc:
            self.assertEqual(exc.status_code, 404)
            return
        self.assertIsInstance(payload, list)
        for item in payload:
            data = item.model_dump()
            for key in {"symbol", "timestamp", "indicator_type", "value", "period"}:
                self.assertIn(key, data)

    def test_indicators_available_endpoint_contract(self) -> None:
        result = self.run_async(get_available_indicators(db=self.session))
        self.assertIn("available_indicators", result)
        self.assertIsInstance(result["available_indicators"], dict)
        self.assertIsInstance(result["total_types"], int)

    def test_error_response_contract(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            self.run_async(
                get_quotes(symbol="NONEXISTENT", limit=100, hours=24, db=self.session)
            )
        self.assertEqual(exc.exception.status_code, 500)
        self.assertIsInstance(exc.exception.detail, str)

    def test_root_endpoint_contract(self) -> None:
        html = self.run_async(read_root())
        self.assertIsInstance(html, str)
        self.assertGreater(len(html), 0)
