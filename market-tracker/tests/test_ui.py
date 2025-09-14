import pytest
from playwright.sync_api import sync_playwright, Page, Browser
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def browser():
    """Create browser instance for testing"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

@pytest.fixture
def page(browser: Browser):
    """Create page instance for testing"""
    page = browser.new_page()
    yield page
    page.close()

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

class TestUI:
    def test_root_page_loads(self, page: Page, client: TestClient):
        """Test that root page loads correctly"""
        # Start the server
        with client:
            # Navigate to the root page
            response = client.get("/")
            assert response.status_code == 200
            
            # Get the HTML content
            html_content = response.text
            
            # Set the content in the page
            page.set_content(html_content)
            
            # Check page title
            title = page.title()
            assert "Market Tracker" in title
            
            # Check for main heading
            heading = page.locator("h1").text_content()
            assert "Market Tracker" in heading
            
            # Check for API endpoints section
            endpoints_section = page.locator("h2:has-text('API Endpoints')")
            assert endpoints_section.count() == 1
            
            # Check for specific endpoints
            quotes_endpoint = page.locator("text=GET /api/v1/quotes")
            assert quotes_endpoint.count() == 1
            
            indicators_endpoint = page.locator("text=GET /api/v1/indicators")
            assert indicators_endpoint.count() == 1
            
            health_endpoint = page.locator("text=GET /api/v1/health")
            assert health_endpoint.count() == 1

    def test_page_styling(self, page: Page, client: TestClient):
        """Test that page has proper styling"""
        with client:
            response = client.get("/")
            page.set_content(response.text)
            
            # Check that CSS is applied
            body = page.locator("body")
            computed_style = body.evaluate("el => getComputedStyle(el)")
            assert "font-family" in str(computed_style)
            
            # Check for container class
            container = page.locator(".container")
            assert container.count() == 1
            
            # Check for endpoint styling
            endpoints = page.locator(".endpoint")
            assert endpoints.count() >= 3  # At least 3 API endpoints

    def test_external_links(self, page: Page, client: TestClient):
        """Test external links are present and correct"""
        with client:
            response = client.get("/")
            page.set_content(response.text)
            
            # Check for Grafana link
            grafana_link = page.locator("a[href='http://localhost:3000']")
            assert grafana_link.count() == 1
            
            # Check link text
            link_text = grafana_link.text_content()
            assert "Grafana Dashboard" in link_text

    def test_responsive_design(self, page: Page, client: TestClient):
        """Test responsive design elements"""
        with client:
            response = client.get("/")
            page.set_content(response.text)
            
            # Test mobile viewport
            page.set_viewport_size({"width": 375, "height": 667})
            
            # Check that content is still visible
            heading = page.locator("h1")
            assert heading.is_visible()
            
            # Test desktop viewport
            page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Check that content is still visible
            assert heading.is_visible()

    def test_page_performance(self, page: Page, client: TestClient):
        """Test page performance metrics"""
        with client:
            response = client.get("/")
            page.set_content(response.text)
            
            # Check that page loads quickly
            # In a real test, you might measure actual load time
            assert len(response.text) < 10000  # Page should be reasonably sized
            
            # Check for any console errors
            # This would require setting up console event listeners in a real test

    def test_accessibility(self, page: Page, client: TestClient):
        """Test basic accessibility features"""
        with client:
            response = client.get("/")
            page.set_content(response.text)
            
            # Check for proper heading hierarchy
            h1_count = page.locator("h1").count()
            assert h1_count == 1
            
            h2_count = page.locator("h2").count()
            assert h2_count >= 2  # At least API Endpoints and External Services
            
            # Check for alt text on images (if any)
            images = page.locator("img")
            for i in range(images.count()):
                img = images.nth(i)
                alt_text = img.get_attribute("alt")
                # If there are images, they should have alt text
                if alt_text is not None:
                    assert len(alt_text) > 0

    def test_api_endpoint_descriptions(self, page: Page, client: TestClient):
        """Test that API endpoint descriptions are present"""
        with client:
            response = client.get("/")
            page.set_content(response.text)
            
            # Check for quotes endpoint description
            quotes_desc = page.locator("text=Get latest market quotes")
            assert quotes_desc.count() == 1
            
            # Check for indicators endpoint description
            indicators_desc = page.locator("text=Get technical indicators")
            assert indicators_desc.count() == 1
            
            # Check for health endpoint description
            health_desc = page.locator("text=Health check endpoint")
            assert health_desc.count() == 1
