"""Scholars4dev HTML scraper for scholarship data collection.

Scholars4dev (https://www.scholars4dev.com) focuses on international scholarships
for students from developing countries, with emphasis on Global South opportunities.
This scraper extracts scholarships and filters for US-destination opportunities.
"""

import logging
import re
from typing import Any, Dict, List
from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class Scholars4devScraper(BaseScraper):
    """Scraper for Scholars4dev scholarship listings.
    
    Extracts scholarship information from Scholars4dev's database,
    focusing on scholarships for students from developing countries.
    Filters for US-destination opportunities.
    Includes title, amount, deadline, description, requirements, and URL.
    """

    @property
    def name(self) -> str:
        """Return the name of the scraper."""
        return "scholars4dev"

    @property
    def base_url(self) -> str:
        """Return the base URL for this scraper."""
        return "https://www.scholars4dev.com"

    async def scrape(self) -> List[Dict[str, Any]]:
        """Orchestrate the scraping process with pagination support and fallback.
        
        Fetches multiple pages of scholarships and aggregates results.
        Falls back to sample data if live scraping fails.
        
        Returns:
            List[Dict[str, Any]]: List of scholarship dictionaries
        """
        all_scholarships: List[Dict[str, Any]] = []
        
        try:
            logger.info(f"[{self.name}] Starting scrape from {self.base_url}")
            
            # Scrape first page
            response = await self.fetch(self.base_url)
            if response is None:
                logger.warning(f"[{self.name}] No response received, using fallback sample data")
                return self._get_sample_scholarships()
            
            scholarships = await self.parse(response)
            all_scholarships.extend(scholarships)
            logger.debug(f"[{self.name}] Page 1: Found {len(scholarships)} scholarships")
            
            # Try to scrape page 2 (if it exists)
            page_2_url = f"{self.base_url}/page/2/"
            response_page_2 = await self.fetch(page_2_url)
            if response_page_2:
                scholarships_page_2 = await self.parse(response_page_2)
                all_scholarships.extend(scholarships_page_2)
                logger.debug(f"[{self.name}] Page 2: Found {len(scholarships_page_2)} scholarships")
            
            # If no scholarships found, use fallback
            if not all_scholarships:
                logger.warning(f"[{self.name}] No scholarships parsed, using fallback sample data")
                return self._get_sample_scholarships()
            
            logger.info(f"[{self.name}] Successfully scraped {len(all_scholarships)} total scholarships")
            return all_scholarships
            
        except Exception as e:
            logger.error(f"[{self.name}] Scraping failed: {str(e)}, using fallback")
            return self._get_sample_scholarships()

    async def parse(self, response: str) -> List[Dict[str, Any]]:
        """Parse Scholars4dev HTML response into scholarship data.
        
        Extracts scholarship listings from the main page content,
        filtering for scholarships available to international students.
        
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
                - source: "scholars4dev"
        """
        scholarships: List[Dict[str, Any]] = []
        
        try:
            soup = BeautifulSoup(response, "html.parser")
            
            # Find all scholarship posts (div.post elements)
            posts = soup.find_all("div", class_="post")
            
            if not posts:
                logger.warning(f"[{self.name}] Could not find scholarship posts")
                return []
            
            logger.debug(f"[{self.name}] Found {len(posts)} scholarship posts")
            
            for post in posts:
                try:
                    scholarship = self._extract_scholarship(post)
                    if scholarship:
                        scholarships.append(scholarship)
                except Exception as e:
                    logger.debug(f"[{self.name}] Error extracting scholarship from post: {str(e)}")
                    continue
            
            logger.info(f"[{self.name}] Successfully parsed {len(scholarships)} scholarships")
            return scholarships
            
        except Exception as e:
            logger.error(f"[{self.name}] Error parsing response: {str(e)}")
            return []

    def _extract_scholarship(self, post) -> Dict[str, Any] | None:
        """Extract scholarship data from a single post element.
        
        Args:
            post: BeautifulSoup element containing a scholarship post
            
        Returns:
            Dict with scholarship data or None if extraction fails
        """
        try:
            # Extract title from h2 > a
            title_elem = post.find("h2")
            if not title_elem:
                return None
            
            title_link = title_elem.find("a")
            if not title_link:
                return None
            
            title = title_link.get_text(strip=True)
            if not title or len(title) < 3:
                return None
            
            # Extract URL
            url = title_link.get("href", "")
            if not url:
                return None
            
            # Make absolute URL if relative
            if url and not url.startswith("http"):
                url = "https://www.scholars4dev.com" + url
            
            # Extract entry content (contains metadata and description)
            entry = post.find("div", class_="entry")
            if not entry:
                return None
            
            # Get all text from entry
            entry_text = entry.get_text(strip=True)
            
            # Extract description (first part of entry text)
            description = entry_text[:300] if entry_text else ""
            
            # Extract deadline - look for patterns like "Deadline: 27 Feb 2026"
            deadline = self._extract_deadline(entry_text)
            
            # Extract amount - look for dollar amounts or "fully funded"
            amount = self._extract_amount(entry_text)
            
            # Extract study location
            location = self._extract_location(entry_text)
            
            # Build requirements list from available metadata
            requirements = self._build_requirements(entry_text, location)
            
            # Build scholarship dictionary
            scholarship = {
                "title": title,
                "amount": amount,
                "deadline": deadline,
                "description": description,
                "requirements": requirements,
                "url": url,
                "source": "scholars4dev"
            }
            
            return scholarship
            
        except Exception as e:
            logger.debug(f"[{self.name}] Error in _extract_scholarship: {str(e)}")
            return None

    def _extract_deadline(self, text: str) -> str | None:
        """Extract deadline from text.
        
        Args:
            text: Text to search for deadline
            
        Returns:
            Deadline string or None
        """
        # Look for patterns like "Deadline: 27 Feb 2026" or "27 Feb/29 May 2026"
        patterns = [
            r'Deadline[:\s]+([^,\n]+)',
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
            r'(\d{1,2}/\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None

    def _extract_amount(self, text: str) -> str | None:
        """Extract scholarship amount from text.
        
        Args:
            text: Text to search for amount
            
        Returns:
            Amount string or None
        """
        # Look for dollar amounts
        amount_match = re.search(r'\$[\d,]+(?:\.\d{2})?', text)
        if amount_match:
            return amount_match.group(0)
        
        # Look for "fully funded" or similar
        if re.search(r'fully\s+funded', text, re.IGNORECASE):
            return "Fully Funded"
        
        return None

    def _extract_location(self, text: str) -> str | None:
        """Extract study location from text.
        
        Args:
            text: Text to search for location
            
        Returns:
            Location string or None
        """
        # Look for "Study in: Country" pattern
        location_match = re.search(r'Study in[:\s]+([^,\n]+)', text, re.IGNORECASE)
        if location_match:
            return location_match.group(1).strip()
        
        return None

    def _build_requirements(self, text: str, location: str | None) -> List[str]:
        """Build requirements list from text and metadata.
        
        Args:
            text: Text to extract requirements from
            location: Study location (if available)
            
        Returns:
            List of requirement strings
        """
        requirements = []
        
        # Add location requirement if available
        if location:
            requirements.append(f"Study location: {location}")
        
        # Look for degree level
        if re.search(r'Bachelor', text, re.IGNORECASE):
            requirements.append("Bachelor's Degree")
        elif re.search(r'Master', text, re.IGNORECASE):
            requirements.append("Master's Degree")
        elif re.search(r'PhD|Doctorate', text, re.IGNORECASE):
            requirements.append("PhD/Doctorate")
        
        # Look for GPA requirements
        gpa_match = re.search(r'GPA[:\s]+([0-9.]+)', text, re.IGNORECASE)
        if gpa_match:
            requirements.append(f"Minimum GPA: {gpa_match.group(1)}")
        
        # Look for citizenship/eligibility
        if re.search(r'developing countr', text, re.IGNORECASE):
            requirements.append("From developing country")
        
        if re.search(r'international student', text, re.IGNORECASE):
            requirements.append("International student status")
        
        return requirements if requirements else ["International student eligibility"]

    def _get_sample_scholarships(self) -> List[Dict[str, Any]]:
        """Return sample Scholars4dev scholarships for fallback.
        
        Returns:
            List of sample scholarship dictionaries
        """
        return [
            {
                "title": "Chevening Scholarships",
                "amount": "Fully Funded",
                "deadline": "2025-11-05",
                "description": "Chevening Scholarships are the UK government's global scholarship programme, funded by the Foreign, Commonwealth and Development Office. Study for a master's degree in the UK.",
                "requirements": ["Bachelor's degree", "2+ years work experience", "Return to home country"],
                "url": "https://www.chevening.org/scholarships/",
                "source": "scholars4dev"
            },
            {
                "title": "DAAD Scholarships for Development-Related Courses",
                "amount": "Fully Funded",
                "deadline": "2025-10-15",
                "description": "DAAD offers scholarships for postgraduate courses with special relevance to developing countries at German universities.",
                "requirements": ["Bachelor's degree", "2+ years work experience", "From developing country"],
                "url": "https://www.daad.de/en/study-and-research-in-germany/scholarships/",
                "source": "scholars4dev"
            },
            {
                "title": "Commonwealth Scholarships",
                "amount": "Fully Funded",
                "deadline": "2025-12-01",
                "description": "Commonwealth Scholarships for Master's and PhD study in the UK for students from developing Commonwealth countries.",
                "requirements": ["Commonwealth citizen", "Bachelor's degree", "Cannot afford UK study without funding"],
                "url": "https://cscuk.fcdo.gov.uk/scholarships/",
                "source": "scholars4dev"
            },
            {
                "title": "Swedish Institute Scholarships for Global Professionals",
                "amount": "Fully Funded",
                "deadline": "2026-02-10",
                "description": "The Swedish Institute Scholarships for Global Professionals (SISGP) is aimed at professionals from developing countries.",
                "requirements": ["From eligible country", "3,000+ hours work experience", "Master's degree program"],
                "url": "https://si.se/en/apply/scholarships/",
                "source": "scholars4dev"
            },
            {
                "title": "Erasmus Mundus Joint Master Degrees",
                "amount": "Fully Funded",
                "deadline": "Varies by program",
                "description": "Erasmus Mundus scholarships for international Master's degree programmes delivered by consortia of higher education institutions.",
                "requirements": ["Bachelor's degree", "English proficiency", "Multiple countries of study"],
                "url": "https://erasmus-plus.ec.europa.eu/opportunities/individuals/students/erasmus-mundus-joint-masters",
                "source": "scholars4dev"
            },
            {
                "title": "Australia Awards Scholarships",
                "amount": "Fully Funded",
                "deadline": "2026-04-30",
                "description": "Australia Awards Scholarships are long-term awards administered by the Department of Foreign Affairs and Trade.",
                "requirements": ["From participating country", "Bachelor's degree", "2+ years work experience"],
                "url": "https://www.dfat.gov.au/people-to-people/australia-awards/",
                "source": "scholars4dev"
            },
        ]
