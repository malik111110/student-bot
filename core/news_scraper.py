import asyncio
import logging
from typing import Any, Dict, List, Optional

from firecrawl import AsyncFirecrawl, Firecrawl

from core.config import settings

logger = logging.getLogger(__name__)


class NewsScraper:
    """News scraper using Firecrawl for Hacker News and tech news websites."""

    def __init__(self):
        if not settings.FIRECRAWL_API_KEY:
            raise ValueError("FIRECRAWL_API_KEY is required but not set")

        self.firecrawl = Firecrawl(api_key=settings.FIRECRAWL_API_KEY)
        self.async_firecrawl = AsyncFirecrawl(api_key=settings.FIRECRAWL_API_KEY)

        # News sources configuration
        self.news_sources = {
            "hacker_news": {
                "url": "https://news.ycombinator.com/",
                "name": "Hacker News",
                "description": "Latest tech news and discussions",
                "fields": ["all"],  # Relevant for all fields
            },
            "techcrunch": {
                "url": "https://techcrunch.com/",
                "name": "TechCrunch",
                "description": "Technology news and startup coverage",
                "fields": ["all"],  # Relevant for all fields
            },
            "arstechnica": {
                "url": "https://arstechnica.com/",
                "name": "Ars Technica",
                "description": "Technology news and analysis",
                "fields": ["all"],  # Relevant for all fields
            },
            "the_verge": {
                "url": "https://www.theverge.com/",
                "name": "The Verge",
                "description": "Technology, science, art, and culture",
                "fields": ["all"],  # Relevant for all fields
            },
        }

        # Field-specific keywords for content filtering
        self.field_keywords = {
            "Sécurité informatique": [
                "cybersecurity",
                "security",
                "hacking",
                "vulnerability",
                "encryption",
                "malware",
                "firewall",
                "penetration testing",
                "ethical hacking",
                "data breach",
                "privacy",
                "authentication",
                "cryptography",
                "infosec",
            ],
            "Intelligence Artificielle": [
                "artificial intelligence",
                "machine learning",
                "deep learning",
                "AI",
                "ML",
                "neural network",
                "computer vision",
                "natural language processing",
                "NLP",
                "robotics",
                "automation",
                "algorithm",
                "data mining",
                "predictive analytics",
            ],
            "RSD": [  # Réseaux et Systèmes Distribués
                "network",
                "distributed systems",
                "cloud computing",
                "microservices",
                "kubernetes",
                "docker",
                "devops",
                "infrastructure",
                "scalability",
                "load balancing",
                "API",
                "web services",
                "system architecture",
            ],
            "Sciences des Données": [
                "data science",
                "big data",
                "analytics",
                "statistics",
                "python",
                "R",
                "database",
                "SQL",
                "data visualization",
                "business intelligence",
                "data mining",
                "predictive modeling",
                "machine learning",
                "AI",
            ],
            "Resin": [  # Réseaux et Systèmes d'Information
                "information systems",
                "network",
                "database",
                "enterprise",
                "ERP",
                "system administration",
                "IT management",
                "infrastructure",
                "business systems",
                "data management",
                "system integration",
            ],
        }

    async def scrape_single_url(
        self, url: str, formats: List[str] = None
    ) -> Dict[str, Any]:
        """Scrape a single URL and return the content."""
        if formats is None:
            formats = ["markdown", "html"]

        try:
            # Correct API call for Firecrawl
            result = await self.async_firecrawl.scrape(url=url, formats=formats)
            return {"success": True, "url": url, "content": result, "error": None}
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {"success": False, "url": url, "content": None, "error": str(e)}

    async def crawl_website(self, url: str, limit: int = 10) -> Dict[str, Any]:
        """Crawl a website and return multiple pages."""
        try:
            # Use the correct Firecrawl crawl API
            result = await self.async_firecrawl.crawl(
                url=url, limit=limit, scrapeOptions={"formats": ["markdown", "html"]}
            )
            return {"success": True, "url": url, "content": result, "error": None}
        except Exception as e:
            logger.error(f"Error crawling {url}: {str(e)}")
            # Fallback to single page scraping if crawling fails
            try:
                logger.info(f"Attempting single page scrape for {url}")
                fallback_result = await self.scrape_single_url(url)
                if fallback_result["success"]:
                    return fallback_result
            except Exception as fallback_error:
                logger.error(
                    f"Fallback scraping also failed for {url}: {str(fallback_error)}"
                )

            return {"success": False, "url": url, "content": None, "error": str(e)}

    async def get_hacker_news(self, limit: int = 5) -> Dict[str, Any]:
        """Get latest news from Hacker News."""
        source = self.news_sources["hacker_news"]
        return await self.crawl_website(source["url"], limit=limit)

    async def get_tech_news(
        self, source: str = "techcrunch", limit: int = 5
    ) -> Dict[str, Any]:
        """Get latest tech news from specified source."""
        if source not in self.news_sources:
            raise ValueError(f"Unknown news source: {source}")

        source_config = self.news_sources[source]
        return await self.crawl_website(source_config["url"], limit=limit)

    async def get_all_tech_news(self, limit_per_source: int = 3) -> Dict[str, Any]:
        """Get news from all configured tech sources."""
        results = {}

        # Get Hacker News
        hn_result = await self.get_hacker_news(limit=limit_per_source)
        results["hacker_news"] = {
            "source": self.news_sources["hacker_news"],
            "result": hn_result,
        }

        # Get other tech news sources
        for source_name in ["techcrunch", "arstechnica", "the_verge"]:
            try:
                tech_result = await self.get_tech_news(
                    source_name, limit=limit_per_source
                )
                results[source_name] = {
                    "source": self.news_sources[source_name],
                    "result": tech_result,
                }
            except Exception as e:
                logger.error(f"Error getting news from {source_name}: {str(e)}")
                results[source_name] = {
                    "source": self.news_sources[source_name],
                    "result": {"success": False, "error": str(e)},
                }

        return results

    def get_field_keywords(self, field: str) -> List[str]:
        """Get keywords for a specific field."""
        return self.field_keywords.get(field, [])

    def filter_content_by_field(self, content: str, field: str) -> str:
        """Filter content to show only field-relevant information."""
        if not content or field not in self.field_keywords:
            return content

        keywords = self.field_keywords[field]
        lines = content.split("\n")
        relevant_lines = []

        for line in lines:
            line_lower = line.lower()
            # Check if line contains any field-specific keywords
            if any(keyword.lower() in line_lower for keyword in keywords):
                relevant_lines.append(line)
            # Also keep lines that are likely headlines (short and capitalized)
            elif len(line.strip()) < 100 and line.strip() and line.strip()[0].isupper():
                relevant_lines.append(line)

        if relevant_lines:
            return "\n".join(relevant_lines)
        else:
            # If no specific content found, return original but with field context
            return (
                f"📚 General tech news (filtered for {field}):\n\n"
                + content[:500]
                + "..."
            )

    async def get_personalized_news(self, field: str, limit: int = 5) -> Dict[str, Any]:
        """Get news personalized for a specific field of study."""
        try:
            # Get general tech news first
            all_news = await self.get_all_tech_news(limit_per_source=2)

            # Filter and combine content based on field
            personalized_content = self._create_personalized_content(all_news, field)

            return {
                "success": True,
                "content": personalized_content,
                "field": field,
                "error": None,
            }
        except Exception as e:
            logger.error(f"Error getting personalized news for {field}: {str(e)}")
            # Return field-specific fallback
            return await self.get_fallback_news_for_field(field)

    def _create_personalized_content(self, all_news: Dict[str, Any], field: str) -> str:
        """Create personalized content from all news sources."""
        field_emoji = self._get_field_emoji(field)
        content_parts = [f"{field_emoji} Personalized News for {field}\n"]

        successful_sources = []
        for source_name, data in all_news.items():
            result = data["result"]
            if result.get("success") and result.get("content"):
                source_info = data["source"]
                raw_content = str(result["content"])

                # Filter content for the field
                filtered_content = self.filter_content_by_field(raw_content, field)

                if filtered_content and len(filtered_content.strip()) > 50:
                    content_parts.append(f"\n🔗 From {source_info['name']}:")
                    content_parts.append(
                        filtered_content[:300] + "..."
                        if len(filtered_content) > 300
                        else filtered_content
                    )
                    successful_sources.append(source_name)

        if successful_sources:
            return "\n".join(content_parts)
        else:
            # No relevant content found, return field-specific fallback
            return self._get_field_specific_fallback(field)

    def _get_field_emoji(self, field: str) -> str:
        """Get emoji for field."""
        field_emojis = {
            "Sécurité informatique": "🔒",
            "Intelligence Artificielle": "🤖",
            "RSD": "🌐",
            "Sciences des Données": "📊",
            "Resin": "💻",
        }
        return field_emojis.get(field, "📰")

    def _get_field_specific_fallback(self, field: str) -> str:
        """Get field-specific fallback content."""
        field_content = {
            "Sécurité informatique": """
🔒 Cybersecurity News Highlights:

• Latest security vulnerabilities and patches
• New malware threats and protection methods
• Cybersecurity best practices and frameworks
• Ethical hacking and penetration testing updates
• Privacy regulations and compliance news
• Encryption and cryptography developments

Stay updated with the latest security trends!
            """,
            "Intelligence Artificielle": """
🤖 AI & Machine Learning News:

• Latest AI model releases and breakthroughs
• Machine learning research and applications
• Computer vision and NLP advancements
• AI ethics and responsible AI development
• Industry AI adoption and case studies
• Open source AI tools and frameworks

Explore the future of artificial intelligence!
            """,
            "RSD": """
🌐 Networks & Distributed Systems News:

• Cloud computing and infrastructure updates
• Microservices and containerization trends
• DevOps tools and best practices
• System scalability and performance
• API design and web services
• Distributed architecture patterns

Build the next generation of distributed systems!
            """,
            "Sciences des Données": """
📊 Data Science News:

• Big data analytics and visualization tools
• Statistical methods and data mining techniques
• Business intelligence and predictive modeling
• Database technologies and data management
• Python, R, and data science libraries
• Industry data science applications

Unlock insights from data!
            """,
            "Resin": """
💻 Information Systems News:

• Enterprise system integration
• Database management and optimization
• IT infrastructure and administration
• Business process automation
• ERP and information system design
• System security and data governance

Manage information systems effectively!
            """,
        }
        return field_content.get(field, self._get_general_fallback())

    def _get_general_fallback(self) -> str:
        """Get general fallback content."""
        return """
📰 Tech News Headlines:

🤖 AI & Machine Learning updates
🔒 Cybersecurity developments  
🌐 Network and cloud technologies
📊 Data science and analytics
💻 Software development trends

For the latest news, please try again later or check sources directly.
        """

    async def get_fallback_news_for_field(self, field: str) -> Dict[str, Any]:
        """Get fallback news for a specific field."""
        return {
            "success": True,
            "content": self._get_field_specific_fallback(field),
            "field": field,
            "error": None,
        }

    async def get_fallback_news(self) -> Dict[str, Any]:
        """Get general fallback news when scraping fails."""
        fallback_news = {
            "success": True,
            "content": self._get_general_fallback(),
            "error": None,
        }
        return fallback_news

    def format_news_for_telegram(
        self, news_data: Dict[str, Any], max_length: int = 4000
    ) -> str:
        """Format news data for Telegram message."""
        if not news_data.get("success"):
            return f"❌ Error fetching news: {news_data.get('error', 'Unknown error')}"

        content = news_data.get("content")
        if not content:
            return "📰 No news content available"

        # Handle different response formats from Firecrawl
        message = "📰 Latest Tech News:\n\n"

        # Try to extract content from various possible formats
        text_content = ""

        if isinstance(content, dict):
            # Try different possible keys
            text_content = (
                content.get("markdown", "")
                or content.get("text", "")
                or content.get("content", "")
                or str(content)
            )
        elif isinstance(content, str):
            text_content = content
        elif hasattr(content, "markdown"):
            text_content = content.markdown
        elif hasattr(content, "text"):
            text_content = content.text
        else:
            text_content = str(content)

        if text_content:
            # Clean up the content for better readability
            text_content = self._clean_scraped_content(text_content)

            # Truncate if too long
            if len(text_content) > max_length - len(message):
                text_content = text_content[: max_length - len(message) - 3] + "..."
            message += text_content
        else:
            message += "Content not available or could not be parsed"

        return message

    def _clean_scraped_content(self, content: str) -> str:
        """Clean scraped content for better readability."""
        import re

        # Remove excessive whitespace
        content = re.sub(r"\n{3,}", "\n\n", content)
        content = re.sub(r"[ \t]+", " ", content)

        # Remove common website navigation elements
        content = re.sub(
            r"(Skip to|Jump to|Go to) (main )?content", "", content, flags=re.IGNORECASE
        )
        content = re.sub(
            r"(Menu|Navigation|Header|Footer)", "", content, flags=re.IGNORECASE
        )

        # Extract headlines and key content (simple approach)
        lines = content.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line and len(line) > 10:  # Skip very short lines
                # Keep lines that look like headlines or content
                if any(
                    keyword in line.lower()
                    for keyword in [
                        "tech",
                        "ai",
                        "software",
                        "computer",
                        "security",
                        "data",
                    ]
                ):
                    cleaned_lines.append(line)
                elif len(line) > 50:  # Keep longer content lines
                    cleaned_lines.append(line)

        # If we have cleaned content, use it; otherwise use original
        if cleaned_lines:
            return "\n\n".join(cleaned_lines[:10])  # Limit to 10 items
        else:
            return content[:1000]  # Fallback to first 1000 chars

    def get_available_sources(self) -> Dict[str, Dict[str, str]]:
        """Get list of available news sources."""
        return self.news_sources


# Global instance
news_scraper = None


def get_news_scraper() -> NewsScraper:
    """Get or create the global news scraper instance."""
    global news_scraper
    if news_scraper is None:
        news_scraper = NewsScraper()
    return news_scraper
