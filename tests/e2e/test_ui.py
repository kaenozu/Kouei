"""
E2E Tests for Kyotei AI
Requires: playwright install
"""
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:5174"

def test_homepage_loads(page: Page):
    """Test that homepage loads successfully"""
    page.goto(BASE_URL)
    expect(page).to_have_title("Vite + React")
    # Check for main heading or logo
    # expect(page.locator("h1")).to_contain_text("競艇AI")

def test_navigation_tabs(page: Page):
    """Test tab navigation"""
    page.goto(BASE_URL)
    
    # Click Today's Races tab
    page.click("text=Today")
    # Should show races list
    # expect(page.locator(".race-card")).to_be_visible()

def test_portfolio_tab(page: Page):
    """Test portfolio display"""
    page.goto(BASE_URL)
    
    # Navigate to Portfolio
    page.click("text=Portfolio")
    
    # Should show balance
    # expect(page.locator("text=残高")).to_be_visible()

def test_api_health(page: Page):
    """Test API is responding"""
    response = page.request.get(f"{BASE_URL.replace('5174', '8001')}/api/status")
    assert response.status == 200
    data = response.json()
    assert "model_loaded" in data

if __name__ == "__main__":
    print("E2E Tests defined. Run with: pytest tests/e2e/test_ui.py")
