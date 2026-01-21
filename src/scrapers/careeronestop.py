"""CareerOneStop scholarship scraper.

Scrapes scholarship data from the US Government's CareerOneStop website.
Provides access to 9,500+ scholarships, fellowships, grants, and financial aid opportunities.
"""

import logging
from typing import Any, Dict, List

from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class CareerOneStopScraper(BaseScraper):
    """Scraper for CareerOneStop scholarship database.
    
    Extracts scholarship data from the CareerOneStop Scholarship Finder tool.
    Handles HTML table parsing with support for multi-line fields and various data formats.
    """

    @property
    def name(self) -> str:
        """Return the name of the scraper."""
        return "CareerOneStop"

    @property
    def base_url(self) -> str:
        """Return the base URL for this scraper."""
        return "https://www.careeronestop.org/toolkit/training/find-scholarships.aspx"

    async def parse(self, response: str) -> List[Dict[str, Any]]:
        """Parse CareerOneStop HTML response into scholarship data.
        
        Extracts scholarship information from the HTML table structure.
        Each row contains: Award Name, Level of Study, Award Type, Award Amount, Deadline.
        
        Args:
            response: HTML response text from fetch()
            
        Returns:
            List[Dict[str, Any]]: List of scholarship dictionaries with standardized fields
        """
        scholarships: List[Dict[str, Any]] = []
        
        try:
            soup = BeautifulSoup(response, "html.parser")
            
            # Find the scholarship table
            table = soup.find("table", class_="cos-table-responsive")
            if not table:
                logger.warning("[CareerOneStop] Could not find scholarship table")
                return scholarships
            
            # Find all table rows (skip header)
            tbody = table.find("tbody")
            if not tbody:
                logger.warning("[CareerOneStop] Could not find table body")
                return scholarships
            
            rows = tbody.find_all("tr")
            logger.debug(f"[CareerOneStop] Found {len(rows)} scholarship rows")
            
            for row in rows:
                try:
                    cells = row.find_all("td")
                    if len(cells) < 5:
                        continue
                    
                    # Extract data from each cell
                    award_cell = cells[0]
                    level_of_study_cell = cells[1]
                    award_type_cell = cells[2]
                    award_amount_cell = cells[3]
                    deadline_cell = cells[4]
                    
                    # Parse Award Name cell (contains title, organization, and description)
                    title = ""
                    organization = ""
                    description = ""
                    url = ""
                    
                    title_link = award_cell.find("a", class_="detailPageLink")
                    if title_link:
                        title = title_link.get_text(strip=True)
                        url = title_link.get("href", "")
                        if url and not url.startswith("http"):
                            url = "https://www.careeronestop.org" + url
                    
                    # Extract organization
                    org_text = award_cell.find_all("div")
                    for div in org_text:
                        text = div.get_text(strip=True)
                        if text.startswith("Organization:"):
                            organization = text.replace("Organization:", "").strip()
                            break
                    
                    # Extract description/purposes
                    for div in org_text:
                        text = div.get_text(strip=True)
                        if text.startswith("Purposes:"):
                            description = text.replace("Purposes:", "").strip()
                            break
                    
                    # Parse Level of Study (can be multiple, comma-separated)
                    level_of_study = self._parse_multiline_field(level_of_study_cell)
                    
                    # Parse Award Type (can be multiple, comma-separated)
                    award_type = self._parse_multiline_field(award_type_cell)
                    
                    # Parse Award Amount (can be multiple, comma-separated)
                    amount = self._parse_multiline_field(award_amount_cell)
                    
                    # Parse Deadline (usually just month or date)
                    deadline = deadline_cell.get_text(strip=True)
                    
                    # Create scholarship dictionary
                    scholarship = {
                        "title": title,
                        "amount": amount,
                        "deadline": deadline,
                        "description": description,
                        "requirements": level_of_study,  # Level of study serves as requirements
                        "url": url,
                        "source": "CareerOneStop",
                        "organization": organization,
                        "award_type": award_type,
                    }
                    
                    scholarships.append(scholarship)
                    
                except Exception as e:
                    logger.warning(f"[CareerOneStop] Error parsing row: {str(e)}")
                    continue
            
            logger.debug(f"[CareerOneStop] Successfully parsed {len(scholarships)} scholarships")
            return scholarships
            
        except Exception as e:
            logger.error(f"[CareerOneStop] Error parsing response: {str(e)}")
            return scholarships

    @staticmethod
    def _parse_multiline_field(cell) -> str:
        """Parse a cell with multiple lines separated by <br> tags.
        
        Args:
            cell: BeautifulSoup cell element
            
        Returns:
            str: Comma-separated values from the cell
        """
        lines = []
        for content in cell.contents:
            text = str(content).strip()
            if text and text != "<br/>" and text != "<br />":
                # Extract text from tags if needed
                if "<" in text:
                    soup = BeautifulSoup(text, "html.parser")
                    text = soup.get_text(strip=True)
                if text:
                    lines.append(text)
        
        return ", ".join(lines) if lines else "N/A"
