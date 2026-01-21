"""Scholarships.com HTML scraper for scholarship data collection.

Uses Playwright browser automation to bypass Cloudflare protection.
"""

import logging
from typing import Any, Dict, List
from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class ScholarshipsComScraper(BaseScraper):
    """Scraper for Scholarships.com scholarship listings.
    
    Extracts scholarship information from Scholarships.com search results,
    including title, amount, deadline, description, requirements, and URL.
    """

    @property
    def name(self) -> str:
        """Return the name of the scraper."""
        return "scholarships_com"

    @property
    def base_url(self) -> str:
        """Return the base URL for this scraper."""
        return "https://www.scholarships.com/financial-aid/college-scholarships/"

    async def _fetch_with_playwright(self, url: str) -> str | None:
        """Fetch page using Playwright to bypass Cloudflare.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None if fetch failed
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error(f"[{self.name}] Playwright not installed. Run: playwright install chromium")
            return None
            
        try:
            logger.info(f"[{self.name}] Launching browser for {url}")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                )
                page = await context.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)
                content = await page.content()
                await browser.close()
                
                logger.info(f"[{self.name}] Got {len(content)} chars via Playwright")
                return content
                
        except Exception as e:
            logger.error(f"[{self.name}] Playwright fetch failed: {e}")
            return None

    async def scrape(self) -> List[Dict[str, Any]]:
        """Override to use Playwright instead of httpx for Cloudflare bypass."""
        try:
            logger.info(f"[{self.name}] Starting scrape from {self.base_url}")
            response = await self._fetch_with_playwright(self.base_url)
            
            if response is None:
                logger.warning(f"[{self.name}] No response, returning empty list")
                return []
            
            return await self.parse(response)
        except Exception as e:
            logger.error(f"[{self.name}] Scraping failed: {e}")
            return []

    async def parse(self, response: str) -> List[Dict[str, Any]]:
        """Parse Scholarships.com HTML response into scholarship data.
        
        Extracts scholarship listings from award-box containers.
        
        Args:
            response: HTML response text from Playwright
            
        Returns:
            List[Dict[str, Any]]: List of scholarship dictionaries
        """
        scholarships: List[Dict[str, Any]] = []
        
        try:
            soup = BeautifulSoup(response, "html.parser")
            
            # Find all award-box containers (the actual scholarship listings)
            scholarship_items = soup.find_all("div", class_="award-box")
            
            logger.debug(f"[{self.name}] Found {len(scholarship_items)} award-box items")
            
            for item in scholarship_items:
                try:
                    scholarship = self._extract_scholarship(item)
                    if scholarship:
                        scholarships.append(scholarship)
                except Exception as e:
                    logger.warning(f"[{self.name}] Error extracting scholarship: {str(e)}")
                    continue
            
            logger.info(f"[{self.name}] Successfully parsed {len(scholarships)} scholarships")
            return scholarships
            
        except Exception as e:
            logger.error(f"[{self.name}] Error parsing response: {str(e)}")
            return []

    def _extract_scholarship(self, item) -> Dict[str, Any] | None:
        """Extract scholarship data from a single award-box element.
        
        Args:
            item: BeautifulSoup element containing scholarship data
            
        Returns:
            Dict with scholarship data or None if extraction fails
        """
        import re
        
        try:
            # Get the full text content
            full_text = item.get_text(" ", strip=True)
            
            # Extract URL and title from the link
            link_elem = item.find("a", href=lambda x: x and "/scholarships/" in x)
            if not link_elem:
                return None
            
            url = link_elem.get("href", "")
            if url and not url.startswith("http"):
                url = "https://www.scholarships.com" + url
            
            # Parse the link text which contains: "# Title Amount $X Deadline DATE Description..."
            link_text = link_elem.get_text(" ", strip=True)
            
            # Remove the leading number
            link_text = re.sub(r"^\d+\s*", "", link_text)
            
            # Extract amount (pattern: $X,XXX or $XX,XXX)
            amount = None
            amount_match = re.search(r"\$[\d,]+", link_text)
            if amount_match:
                amount = amount_match.group(0)
            
            # Extract deadline (pattern: Month Day, Year)
            deadline = None
            deadline_match = re.search(
                r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
                link_text
            )
            if deadline_match:
                deadline = deadline_match.group(0)
            
            # Extract title: text before "Amount" keyword
            title = None
            amount_idx = link_text.find("Amount")
            if amount_idx > 0:
                title = link_text[:amount_idx].strip()
            else:
                # Fallback: use text before $ sign
                dollar_idx = link_text.find("$")
                if dollar_idx > 0:
                    title = link_text[:dollar_idx].strip()
                else:
                    title = link_text[:50].strip()
            
            # Extract description: text after the deadline
            description = None
            if deadline_match:
                desc_start = deadline_match.end()
                description = link_text[desc_start:].strip()
                # Limit description length
                if len(description) > 300:
                    description = description[:300] + "..."
            
            if not title:
                return None
            
            return {
                "title": title,
                "amount": amount,
                "deadline": deadline,
                "description": description,
                "requirements": None,  # Not available on listing page
                "url": url,
                "source": "scholarships.com"
            }
            
        except Exception as e:
            logger.warning(f"[{self.name}] Error in _extract_scholarship: {str(e)}")
            return None
