"""InternationalScholarships.com HTML scraper for scholarship data collection."""

import logging
from typing import Any, Dict, List
from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class InternationalScholarshipsComScraper(BaseScraper):
    """Scraper for InternationalScholarships.com scholarship listings.
    
    Extracts scholarship information for international students studying in the US,
    including title, amount, deadline, description, requirements, and URL.
    """

    @property
    def name(self) -> str:
        """Return the name of the scraper."""
        return "intl_scholarships_com"

    @property
    def base_url(self) -> str:
        """Return the base URL for this scraper.
        
        Uses the US location filter (254) to focus on scholarships for studying IN the US.
        """
        return "https://www.internationalscholarships.com/scholarships/US/"

    async def parse(self, response: str) -> List[Dict[str, Any]]:
        """Parse InternationalScholarships.com HTML response into scholarship data.
        
        Extracts scholarship listings from the search results page table,
        handling the typical structure of InternationalScholarships.com listings.
        
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
                - source: "internationalscholarships.com"
        """
        scholarships: List[Dict[str, Any]] = []
        
        try:
            soup = BeautifulSoup(response, "html.parser")
            
            # Find the table containing scholarship listings
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
                    logger.warning(f"[{self.name}] Error extracting scholarship: {str(e)}")
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
            
            # First cell contains title and link
            title_cell = cells[0]
            
            # Find all links in the title cell and get the last one (actual scholarship link)
            links = title_cell.find_all("a")
            if not links:
                return None
            
            # The last link is typically the scholarship title link
            title_elem = links[-1]
            title = title_elem.get_text(strip=True)
            
            if not title:
                return None
            
            # Extract URL from the link
            url = title_elem.get("href")
            if url and not url.startswith("http"):
                url = "https://www.internationalscholarships.com" + url
            
            # Second cell contains description
            description = None
            if len(cells) > 1:
                desc_cell = cells[1]
                description = desc_cell.get_text(strip=True)
                # Truncate if too long
                if description and len(description) > 500:
                    description = description[:500] + "..."
            
            # Third cell contains restrictions/requirements
            requirements = None
            if len(cells) > 2:
                req_cell = cells[2]
                requirements = req_cell.get_text(strip=True)
            
            # Try to extract amount and deadline from description or requirements
            amount = None
            deadline = None
            
            if description:
                # Look for dollar amounts
                import re
                amount_match = re.search(r'\$[\d,]+(?:\.\d{2})?', description)
                if amount_match:
                    amount = amount_match.group(0)
                
                # Look for deadline patterns (e.g., "Deadline: January 15")
                deadline_match = re.search(
                    r'(?:deadline|due|closes?|expires?)[:\s]+([^,\n]+)',
                    description,
                    re.IGNORECASE
                )
                if deadline_match:
                    deadline = deadline_match.group(1).strip()
            
            # Build scholarship dictionary
            scholarship = {
                "title": title,
                "amount": amount,
                "deadline": deadline,
                "description": description,
                "requirements": requirements,
                "url": url,
                "source": "internationalscholarships.com"
            }
            
            return scholarship
            
        except Exception as e:
            logger.warning(f"[{self.name}] Error in _extract_scholarship: {str(e)}")
            return None
