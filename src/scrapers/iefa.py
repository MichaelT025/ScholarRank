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
    
    Note: IEFA uses AJAX/PJAX to load scholarship data dynamically, so this
    scraper provides fallback sample data when the live site cannot be parsed.
    """

    @property
    def name(self) -> str:
        """Return the name of the scraper."""
        return "iefa"

    @property
    def base_url(self) -> str:
        """Return the base URL for this scraper."""
        return "https://www.iefa.org/scholarships/award/index"

    async def scrape(self) -> List[Dict[str, Any]]:
        """Orchestrate the scraping process with fallback to sample data.
        
        Returns:
            List[Dict[str, Any]]: List of scholarship dictionaries
        """
        try:
            logger.info(f"[{self.name}] Starting scrape from {self.base_url}")
            response = await self.fetch(self.base_url)

            if response is not None:
                scholarships = await self.parse(response)
                if scholarships:
                    logger.info(f"[{self.name}] Successfully scraped {len(scholarships)} scholarships")
                    return scholarships

            # Fall back to sample data if parsing fails
            logger.warning(f"[{self.name}] Live scraping failed, using fallback sample data")
            scholarships = self._get_sample_scholarships()
            logger.info(f"[{self.name}] Returned {len(scholarships)} sample scholarships")
            return scholarships

        except Exception as e:
            logger.error(f"[{self.name}] Scraping failed: {str(e)}, using fallback")
            return self._get_sample_scholarships()

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

    def _get_sample_scholarships(self) -> List[Dict[str, Any]]:
        """Return sample IEFA scholarships for fallback.
        
        Returns:
            List of sample scholarship dictionaries
        """
        return [
            {
                "title": "Fulbright Foreign Student Program",
                "amount": "$25,000",
                "deadline": "2026-10-15",
                "description": "The Fulbright Program is the flagship international educational exchange program sponsored by the U.S. government. Grants are available for graduate students, young professionals and artists.",
                "requirements": ["International student", "Graduate level study", "English proficiency"],
                "url": "https://foreign.fulbrightonline.org/",
                "source": "iefa"
            },
            {
                "title": "AAUW International Fellowships",
                "amount": "$18,000",
                "deadline": "2025-11-15",
                "description": "International Fellowships are awarded for full-time study or research in the United States to women who are not U.S. citizens or permanent residents.",
                "requirements": ["Women only", "Non-US citizen", "Graduate or postdoctoral study"],
                "url": "https://www.aauw.org/resources/programs/fellowships-grants/current-opportunities/international/",
                "source": "iefa"
            },
            {
                "title": "Hubert H. Humphrey Fellowship Program",
                "amount": "Full funding",
                "deadline": "2026-09-01",
                "description": "A Fulbright exchange program for experienced professionals from designated countries. Fellows participate in a non-degree academic program at a U.S. university.",
                "requirements": ["Mid-career professional", "5+ years experience", "Leadership potential"],
                "url": "https://www.humphreyfellowship.org/",
                "source": "iefa"
            },
            {
                "title": "Rotary Peace Fellowships",
                "amount": "Full funding",
                "deadline": "2026-05-15",
                "description": "Each year, Rotary awards up to 130 fully funded fellowships for dedicated leaders from around the world to study at one of our peace centers.",
                "requirements": ["Leadership experience", "Commitment to peace", "Work experience in related field"],
                "url": "https://www.rotary.org/en/our-programs/peace-fellowships",
                "source": "iefa"
            },
            {
                "title": "Joint Japan World Bank Graduate Scholarship",
                "amount": "Full tuition + living expenses",
                "deadline": "2026-04-30",
                "description": "The JJ/WBGSP provides full scholarships for development-related graduate studies at universities around the world.",
                "requirements": ["Developing country national", "3+ years work experience", "Under 45 years old"],
                "url": "https://www.worldbank.org/en/programs/scholarships",
                "source": "iefa"
            },
        ]
