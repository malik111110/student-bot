#!/usr/bin/env python3
"""
Test script for the news scraper functionality.
This script tests the news scraper without requiring the full bot setup.
"""

import asyncio
import os
import pytest
from core.news_scraper import get_news_scraper

@pytest.mark.asyncio
async def test_news_scraper_functionality():
    """Test the news scraper functionality."""
    print("🧪 Testing News Scraper...")
    
    # Check if API key is set
    api_key = os.getenv('FIRECRAWL_API_KEY')
    if not api_key:
        pytest.skip("FIRECRAWL_API_KEY not set in environment variables")
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    try:
        # Initialize scraper
        scraper = get_news_scraper()
        print("✅ News scraper initialized successfully")
        
        # Test getting available sources
        sources = scraper.get_available_sources()
        print(f"✅ Available sources: {list(sources.keys())}")
        
        # Test scraping a simple URL (using a test URL)
        print("\n🔍 Testing single URL scraping...")
        test_url = "https://httpbin.org/html"  # Simple test URL
        result = await scraper.scrape_single_url(test_url, formats=['markdown'])
        
        assert result['success']
        assert len(str(result['content'])) > 0
        
        print("✅ Single URL scraping successful")
        
        # Test getting news sources info
        print("\n📰 Testing news sources...")
        for source_name, source_info in sources.items():
            print(f"   {source_name}: {source_info['name']} - {source_info['description']}")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        pytest.fail(f"Error during testing: {str(e)}")