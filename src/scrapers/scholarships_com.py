"""Scholarships.com HTML scraper for scholarship data collection."""

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
        return "https://www.scholarships.com/scholarship-search"

    async def parse(self, response: str) -> List[Dict[str, Any]]:
        """Parse Scholarships.com HTML response into scholarship data.
        
        Extracts scholarship listings from the search results page,
        handling the typical structure of Scholarships.com listings.
        
        Args:
            response: HTML response text from fetch()
            
        Returns:
            List[Dict[str, Any]]: List of scholarship dictionaries with fields:
                - title: Scholarship name
                - amount: Award amount (if available)
                - deadline: Application deadline (if available)
                - description: Scholarship description
                - requirements: Eligibility requirements
                - url: Link to scholarship details
                - source: "scholarships.com"
        """
        scholarships: List[Dict[str, Any]] = []
        
        try:
            soup = BeautifulSoup(response, "html.parser")
            
            # Find all scholarship listing containers
            # Scholarships.com typically uses divs with class containing "scholarship" or similar
            scholarship_items = soup.find_all("div", class_=lambda x: x and "scholarship" in x.lower())
            
            if not scholarship_items:
                # Fallback: look for article tags or other common containers
                scholarship_items = soup.find_all("article")
            
            if not scholarship_items:
                # Another fallback: look for divs with data attributes
                scholarship_items = soup.find_all("div", {"data-scholarship": True})
            
            logger.debug(f"[{self.name}] Found {len(scholarship_items)} scholarship items")
            
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
        """Extract scholarship data from a single listing item.
        
        Args:
            item: BeautifulSoup element containing scholarship data
            
        Returns:
            Dict with scholarship data or None if extraction fails
        """
        try:
            # Extract title - typically in h2, h3, or a tag
            title_elem = item.find(["h2", "h3", "a"])
            title = title_elem.get_text(strip=True) if title_elem else None
            
            if not title:
                return None
            
            # Extract URL - look for href in links
            url = None
            link_elem = item.find("a", href=True)
            if link_elem:
                url = link_elem.get("href")
                # Make absolute URL if relative
                if url and not url.startswith("http"):
                    url = "https://www.scholarships.com" + url
            
            # Extract amount - look for dollar signs or "amount" keywords
            amount = None
            amount_elem = item.find(string=lambda x: x and ("$" in x or "amount" in x.lower()))
            if amount_elem:
                amount = amount_elem.get_text(strip=True)
            
            # Extract deadline - look for date patterns or "deadline" keywords
            deadline = None
            deadline_elem = item.find(string=lambda x: x and ("deadline" in x.lower() or "due" in x.lower()))
            if deadline_elem:
                deadline = deadline_elem.get_text(strip=True)
            
            # Extract description - typically in p tags
            description_parts = []
            for p in item.find_all("p"):
                text = p.get_text(strip=True)
                if text and len(text) > 10:  # Filter out very short text
                    description_parts.append(text)
            description = " ".join(description_parts[:2]) if description_parts else None
            
            # Extract requirements - look for lists or specific requirement sections
            requirements = None
            req_elem = item.find(string=lambda x: x and "require" in x.lower())
            if req_elem:
                # Try to get the parent container with requirements
                req_container = req_elem.find_parent(["div", "section", "ul"])
                if req_container:
                    requirements = req_container.get_text(strip=True)
            
            # Build scholarship dictionary
            scholarship = {
                "title": title,
                "amount": amount,
                "deadline": deadline,
                "description": description,
                "requirements": requirements,
                "url": url,
                "source": "scholarships.com"
            }
            
            return scholarship
            
        except Exception as e:
            logger.warning(f"[{self.name}] Error in _extract_scholarship: {str(e)}")
            return None
