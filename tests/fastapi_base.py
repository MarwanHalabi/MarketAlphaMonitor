import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List
from unittest import TestCase

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

MARKET_TRACKER_ROOT = Path(__file__).resolve().parents[1] / "market-tracker"
if str(MARKET_TRACKER_ROOT) not in sys.path:
    sys.path.insert(0, str(MARKET_TRACKER_ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///./market_tracker_test.db")

from app.db import Base, get_db
from app.main import app
from app.models import Indicator, Price


class FastAPITestCase(TestCase):
    """Base ``unittest`` test case for FastAPI endpoint testing."""

    database_url = "sqlite:///./market_tracker_test.db"
    load_sample_data = True

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.engine = create_engine(
            cls.database_url,
            connect_args={"check_same_thread": False},
        )
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        def override_get_db():
            db = cls.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db

    @classmethod
    def tearDownClass(cls) -> None:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=cls.engine)
        cls.engine.dispose()
        db_path = Path(cls.database_url.replace("sqlite:///", ""))
        if db_path.exists():
            db_path.unlink()
        super().tearDownClass()

    def setUp(self) -> None:
        super().setUp()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.session = self.SessionLocal()
        self._clear_tables()
        if self.load_sample_data:
            self._insert_sample_data()

    def tearDown(self) -> None:
        self.session.close()
        self.loop.close()
        asyncio.set_event_loop(None)
        super().tearDown()

    def run_async(self, coroutine):
        return self.loop.run_until_complete(coroutine)

    def _clear_tables(self) -> None:
        self.session.query(Indicator).delete()
        self.session.query(Price).delete()
        self.session.commit()

    def _insert_sample_data(self) -> None:
        now = datetime.now(timezone.utc)
        prices: List[Price] = [
            Price(
                symbol="AAPL",
                ts=now - timedelta(minutes=offset),
                o=150.0 + offset,
                h=151.0 + offset,
                l=149.5 + offset,
                c=150.5 + offset,
                v=1_000_000 + offset * 10_000,
            )
            for offset in range(1, 4)
        ]
        prices.append(
            Price(
                symbol="MSFT",
                ts=now - timedelta(minutes=5),
                o=300.0,
                h=301.0,
                l=299.5,
                c=300.5,
                v=800_000,
            )
        )

        indicators: List[Indicator] = [
            Indicator(
                symbol="AAPL",
                ts=prices[0].ts,
                indicator_type="ema",
                value=150.25,
                period=21,
            ),
            Indicator(
                symbol="AAPL",
                ts=prices[0].ts,
                indicator_type="rsi",
                value=65.5,
                period=14,
            ),
        ]

        self.session.add_all(prices + indicators)
        self.session.commit()
