import re
import sys
from pathlib import Path

import os
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
from tests.fastapi_base import FastAPITestCase


class UITests(FastAPITestCase):
    load_sample_data = False

    def setUp(self) -> None:
        super().setUp()
        self.html = self.run_async(read_root())

    def test_root_page_loads(self) -> None:
        self.assertIn("<h1>📈 Market Tracker</h1>", self.html)
        self.assertIn("API Endpoints", self.html)
        self.assertIn("External Services", self.html)

    def test_page_styling(self) -> None:
        self.assertIn("body { font-family: Arial, sans-serif; margin: 40px; }", self.html)
        self.assertIn("class=\"container\"", self.html)
        self.assertGreaterEqual(self.html.count("class=\"endpoint\""), 3)

    def test_external_links(self) -> None:
        self.assertIn("href=\"http://localhost:3000\"", self.html)
        self.assertIn("Grafana Dashboard", self.html)

    def test_content_size_is_reasonable(self) -> None:
        self.assertLess(len(self.html), 10000)

    def test_accessibility_structure(self) -> None:
        h1_tags = re.findall(r"<h1[\\s>].*?</h1>", self.html)
        h2_tags = re.findall(r"<h2[\\s>].*?</h2>", self.html)
        self.assertEqual(len(h1_tags), 1)
        self.assertGreaterEqual(len(h2_tags), 2)

    def test_images_have_alt_text_if_present(self) -> None:
        images = re.findall(r"<img[^>]*>", self.html)
        for image in images:
            if "alt=" in image:
                alt_value = re.search(r"alt=\"([^\"]*)\"", image)
                self.assertIsNotNone(alt_value)
                self.assertTrue(alt_value.group(1))

    def test_api_endpoint_descriptions(self) -> None:
        self.assertIn("Get latest market quotes", self.html)
        self.assertIn("Get technical indicators (EMA, RSI)", self.html)
        self.assertIn("Health check endpoint", self.html)
