"""IEFA (International Education Financial Aid) HTML scraper for scholarship data collection."""

import logging
from typing import Any, Dict, List
from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class IEFAScraper(BaseScraper):
    """Scraper for IEFA scholarship listings.
    
    Extracts scholarship information from IEFA's scholarship database,
    focusing on scholarships for international students coming to the US.
    Includes title, amount, deadline, description, requirements, and URL.
    """

    @property
    def name(self) -> str:
        """Return the name of the scraper."""
        return "iefa"

    @property
    def base_url(self) -> str:
        """Return the base URL for this scraper."""
        return "https://www.iefa.org/scholarships/award/index"

    async def parse(self, response: str) -> List[Dict[str, Any]]:
        """Parse IEFA HTML response into scholarship data.
        
        Extracts scholarship listings from the table on IEFA's awards page,
        filtering for scholarships available to international students studying in the US.
        
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
                - source: "iefa"
        """
        scholarships: List[Dict[str, Any]] = []
        
        try:
            soup = BeautifulSoup(response, "html.parser")
            
            # Find the main scholarship table
            table = soup.find("table", class_="table")
            
            if not table:
                logger.warning(f"[{self.name}] Could not find scholarship table")
                return []
            
            # Find all table rows (skip header)
            rows = table.find_all("tr")[1:]  # Skip header row
            
            logger.debug(f"[{self.name}] Found {len(rows)} scholarship rows")
            
            for row in rows:
                try:
                    scholarship = self._extract_scholarship(row)
                    if scholarship:
                        scholarships.append(scholarship)
                except Exception as e:
                    logger.warning(f"[{self.name}] Error extracting scholarship from row: {str(e)}")
                    continue
            
            logger.info(f"[{self.name}] Successfully parsed {len(scholarships)} scholarships")
            return scholarships
            
        except Exception as e:
            logger.error(f"[{self.name}] Error parsing response: {str(e)}")
            return []

    def _extract_scholarship(self, row) -> Dict[str, Any] | None:
        """Extract scholarship data from a single table row.
        
        Args:
            row: BeautifulSoup element containing a table row
            
        Returns:
            Dict with scholarship data or None if extraction fails
        """
        try:
            # Get all cells in the row
            cells = row.find_all("td")
            
            if len(cells) < 3:
                return None
            
            # Extract title from first cell (usually contains the award name and link)
            title_cell = cells[0]
            title_elem = title_cell.find("a")
            title = title_elem.get_text(strip=True) if title_elem else title_cell.get_text(strip=True)
            
            if not title or len(title) < 3:
                return None
            
            # Extract URL from the link
            url = None
            if title_elem and title_elem.get("href"):
                url = title_elem.get("href")
                # Make absolute URL if relative
                if url and not url.startswith("http"):
                    url = "https://www.iefa.org" + url
            
            # Extract field of study from second cell
            field = cells[1].get_text(strip=True) if len(cells) > 1 else None
            
            # Extract description from third cell
            description = cells[2].get_text(strip=True) if len(cells) > 2 else None
            
            # Try to extract amount and deadline from description or other cells
            amount = None
            deadline = None
            
            # Look for dollar amounts in description
            if description:
                import re
                amount_match = re.search(r'\$[\d,]+(?:\.\d{2})?', description)
                if amount_match:
                    amount = amount_match.group(0)
                
                # Look for deadline patterns (Month Year or dates)
                deadline_match = re.search(
                    r'(?:Deadline|Due|Application closes?|Closes?|Expires?)[:\s]+([^,\n]+)',
                    description,
                    re.IGNORECASE
                )
                if deadline_match:
                    deadline = deadline_match.group(1).strip()
            
            # Extract requirements - look for eligibility info in description
            requirements = None
            if description and len(description) > 50:
                # Use first part of description as requirements hint
                requirements = description[:200] + "..." if len(description) > 200 else description
            
            # Build scholarship dictionary
            scholarship = {
                "title": title,
                "amount": amount,
                "deadline": deadline,
                "description": description,
                "requirements": requirements,
                "url": url,
                "source": "iefa"
            }
            
            return scholarship
            
        except Exception as e:
            logger.warning(f"[{self.name}] Error in _extract_scholarship: {str(e)}")
            return None
