import pytest
from src.apify_scraper import ApifyJobScraper

def test_normalize_items():
    scraper = ApifyJobScraper(api_token="dummy_token")
    
    raw_items = [
        {
            "jobTitle": "Lead Test Automation Engineer",
            "companyName": "Google",
            "location": "Remote, USA",
            "jobDescription": "We are looking for a Playwright and Selenium lead.",
            "jobUrl": "https://careers.google.com/jobs/123",
            "postedAt": "2 days ago"
        },
        {
            "title": "Senior SDET",
            "company": "Microsoft",
            "location": "Seattle, WA",
            "description": "Looking for NUnit and C# skills.",
            "url": "https://careers.microsoft.com/jobs/456",
            "posted_date": "1 week ago"
        }
    ]
    
    normalized = scraper._normalize_items(raw_items)
    
    assert len(normalized) == 2
    
    # Check item 1
    assert normalized[0]["title"] == "Lead Test Automation Engineer"
    assert normalized[0]["company"] == "Google"
    assert normalized[0]["location"] == "Remote, USA"
    assert "Playwright" in normalized[0]["description"]
    assert normalized[0]["url"] == "https://careers.google.com/jobs/123"
    assert normalized[0]["posted_at"] == "2 days ago"
    
    # Check item 2
    assert normalized[1]["title"] == "Senior SDET"
    assert normalized[1]["company"] == "Microsoft"
    assert normalized[1]["location"] == "Seattle, WA"
    assert "NUnit" in normalized[1]["description"]
    assert normalized[1]["url"] == "https://careers.microsoft.com/jobs/456"
    assert normalized[1]["posted_at"] == "1 week ago"

def test_missing_api_token():
    scraper = ApifyJobScraper(api_token="")
    with pytest.raises(ValueError):
        scraper.scrape_jobs("SDET", limit=5)

