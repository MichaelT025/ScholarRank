"""Fastweb scholarship scraper.

Fastweb (https://www.fastweb.com) is a free scholarship matching service
with 1.5M+ scholarships in their database.

Note: Fastweb's official API (https://developers.fastweb.it/) requires
registration and API keys. This implementation provides a fallback with
sample data for development/testing purposes.

TODO: Integrate with official Fastweb API once credentials are available.
Set FASTWEB_API_KEY environment variable to enable live API calls.
"""

import json
import logging
import os
from typing import Any, Dict, List

from src.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class FastwebScraper(BaseScraper):
    """Scraper for Fastweb scholarships.
    
    Fastweb is one of the largest scholarship databases with 1.5M+ scholarships.
    This implementation uses sample data as a fallback since the official API
    requires registration.
    """

    @property
    def name(self) -> str:
        """Return the name of the scraper."""
        return "fastweb"

    @property
    def base_url(self) -> str:
        """Return the base URL for this scraper.
        
        Note: The official Fastweb API requires authentication credentials.
        This URL is a placeholder that will fail gracefully and fall back to
        sample data. To use the live API, set FASTWEB_API_KEY environment variable
        and update this to the authenticated endpoint.
        
        TODO: Replace with actual API endpoint once credentials are available.
        Expected format: https://api.fastweb.com/v1/scholarships?api_key={key}
        """
        api_key = os.getenv("FASTWEB_API_KEY")
        if api_key:
            return f"https://api.fastweb.com/v1/scholarships?api_key={api_key}"
        # Return a placeholder that will fail gracefully
        return "https://www.fastweb.com/api/scholarships"

    async def scrape(self) -> List[Dict[str, Any]]:
        """Orchestrate the scraping process with fallback to sample data.
        
        Attempts to fetch from the API, but gracefully falls back to sample
        data if the API is unavailable or not configured.
        
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

            # Fall back to sample data if API is unavailable
            logger.warning(f"[{self.name}] API unavailable, using fallback sample data")
            scholarships = self._get_sample_scholarships()
            logger.info(f"[{self.name}] Returned {len(scholarships)} sample scholarships")
            return scholarships

        except Exception as e:
            logger.error(f"[{self.name}] Scraping failed: {str(e)}, using fallback")
            return self._get_sample_scholarships()

    async def parse(self, response: str) -> List[Dict[str, Any]]:
        """Parse response content into scholarship data.
        
        Args:
            response: Response text from fetch()
            
        Returns:
            List[Dict[str, Any]]: List of scholarship dictionaries with fields:
                - title: Scholarship name
                - amount: Award amount (int or string)
                - deadline: Application deadline (ISO format or string)
                - description: Scholarship description
                - requirements: List of eligibility requirements
                - url: Direct link to scholarship
                - source: "fastweb"
        """
        try:
            # Try to parse as JSON (for API responses)
            data = json.loads(response)
            scholarships = self._extract_scholarships_from_api(data)
            
            if scholarships:
                logger.info(f"[{self.name}] Parsed {len(scholarships)} scholarships from API")
                return scholarships
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"[{self.name}] Failed to parse response as JSON: {str(e)}")
        
        # Fallback to sample data if API is unavailable
        logger.warning(f"[{self.name}] Using fallback sample data (API unavailable)")
        return self._get_sample_scholarships()

    def _extract_scholarships_from_api(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract scholarships from API response.
        
        Args:
            data: Parsed JSON response from Fastweb API
            
        Returns:
            List of standardized scholarship dictionaries
        """
        scholarships = []
        
        # Handle different possible API response structures
        items = data.get("scholarships", data.get("data", data.get("results", [])))
        
        if not isinstance(items, list):
            return []
        
        for item in items:
            try:
                scholarship = {
                    "title": item.get("title", ""),
                    "amount": item.get("amount", item.get("award_amount", 0)),
                    "deadline": item.get("deadline", item.get("application_deadline", "")),
                    "description": item.get("description", item.get("summary", "")),
                    "requirements": item.get("requirements", item.get("eligibility", [])),
                    "url": item.get("url", item.get("link", "")),
                    "source": "fastweb",
                }
                
                # Only include if we have at least title and URL
                if scholarship["title"] and scholarship["url"]:
                    scholarships.append(scholarship)
                    
            except (KeyError, TypeError) as e:
                logger.debug(f"[{self.name}] Error parsing scholarship item: {str(e)}")
                continue
        
        return scholarships

    def _get_sample_scholarships(self) -> List[Dict[str, Any]]:
        """Return sample scholarship data for development/testing.
        
        This is used when the API is unavailable or not configured.
        
        Returns:
            List of sample scholarship dictionaries
        """
        return [
            {
                "title": "Fastweb Scholarship - STEM Excellence",
                "amount": 5000,
                "deadline": "2025-06-30",
                "description": "Award for students pursuing degrees in Science, Technology, Engineering, or Mathematics with demonstrated academic excellence.",
                "requirements": [
                    "Minimum 3.5 GPA",
                    "Full-time student status",
                    "U.S. citizen or permanent resident",
                    "STEM major",
                ],
                "url": "https://www.fastweb.com/scholarships/stem-excellence",
                "source": "fastweb",
            },
            {
                "title": "Fastweb Scholarship - Community Service",
                "amount": 3000,
                "deadline": "2025-05-15",
                "description": "Recognizes students who have demonstrated significant commitment to community service and volunteer work.",
                "requirements": [
                    "Minimum 3.0 GPA",
                    "100+ hours of community service",
                    "Essay on community impact",
                    "High school senior or college student",
                ],
                "url": "https://www.fastweb.com/scholarships/community-service",
                "source": "fastweb",
            },
            {
                "title": "Fastweb Scholarship - First Generation",
                "amount": 2500,
                "deadline": "2025-07-31",
                "description": "For first-generation college students pursuing higher education.",
                "requirements": [
                    "First-generation college student",
                    "Minimum 2.5 GPA",
                    "Enrolled or planning to enroll in accredited institution",
                    "U.S. citizen",
                ],
                "url": "https://www.fastweb.com/scholarships/first-generation",
                "source": "fastweb",
            },
            {
                "title": "Fastweb Scholarship - Business Leaders",
                "amount": 4000,
                "deadline": "2025-04-30",
                "description": "For students pursuing business degrees with leadership potential and entrepreneurial spirit.",
                "requirements": [
                    "Business major or minor",
                    "Minimum 3.2 GPA",
                    "Leadership experience",
                    "Essay on business vision",
                ],
                "url": "https://www.fastweb.com/scholarships/business-leaders",
                "source": "fastweb",
            },
            {
                "title": "Fastweb Scholarship - Healthcare Professionals",
                "amount": 6000,
                "deadline": "2025-08-15",
                "description": "Supporting students pursuing careers in healthcare, nursing, medicine, and related fields.",
                "requirements": [
                    "Healthcare-related major",
                    "Minimum 3.3 GPA",
                    "Clinical experience or volunteer work",
                    "Commitment to healthcare service",
                ],
                "url": "https://www.fastweb.com/scholarships/healthcare-professionals",
                "source": "fastweb",
            },
        ]
