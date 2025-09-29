import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from core.news_scraper import get_news_scraper

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/sources")
async def get_news_sources():
    """Get list of available news sources."""
    try:
        scraper = get_news_scraper()
        sources = scraper.get_available_sources()
        return {"sources": sources}
    except Exception as e:
        logger.error(f"Error getting news sources: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error getting news sources: {str(e)}"
        )


@router.get("/hackernews")
async def get_hacker_news(
    limit: int = Query(5, ge=1, le=20, description="Number of articles to fetch")
):
    """Get latest news from Hacker News."""
    try:
        scraper = get_news_scraper()
        result = await scraper.get_hacker_news(limit=limit)
        return result
    except Exception as e:
        logger.error(f"Error fetching Hacker News: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching Hacker News: {str(e)}"
        )


@router.get("/technews/{source}")
async def get_tech_news(
    source: str,
    limit: int = Query(5, ge=1, le=20, description="Number of articles to fetch"),
):
    """Get tech news from a specific source."""
    try:
        scraper = get_news_scraper()
        available_sources = scraper.get_available_sources()

        if source not in available_sources:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown source: {source}. Available sources: {list(available_sources.keys())}",
            )

        result = await scraper.get_tech_news(source, limit=limit)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching tech news from {source}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching tech news: {str(e)}"
        )


@router.get("/all")
async def get_all_news(
    limit_per_source: int = Query(
        3, ge=1, le=10, description="Number of articles per source"
    )
):
    """Get news from all available sources."""
    try:
        scraper = get_news_scraper()
        result = await scraper.get_all_tech_news(limit_per_source=limit_per_source)
        return result
    except Exception as e:
        logger.error(f"Error fetching all news: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching all news: {str(e)}"
        )


@router.post("/scrape")
async def scrape_url(
    url: str,
    formats: List[str] = Query(["markdown", "html"], description="Output formats"),
):
    """Scrape a specific URL."""
    try:
        scraper = get_news_scraper()
        result = await scraper.scrape_single_url(url, formats=formats)
        return result
    except Exception as e:
        logger.error(f"Error scraping URL {url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scraping URL: {str(e)}")


@router.post("/crawl")
async def crawl_website(
    url: str,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of pages to crawl"),
):
    """Crawl a website for multiple pages."""
    try:
        scraper = get_news_scraper()
        result = await scraper.crawl_website(url, limit=limit)
        return result
    except Exception as e:
        logger.error(f"Error crawling website {url}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error crawling website: {str(e)}")
