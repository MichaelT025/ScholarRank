"""Base scraper class for scholarship data collection."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for scholarship scrapers.
    
    Provides common functionality for fetching and parsing scholarship data
    from various sources, including rate limiting, retry logic, and error handling.
    """

    def __init__(self, rate_limit_delay: float = 1.0, max_retries: int = 3):
        """Initialize the scraper.
        
        Args:
            rate_limit_delay: Delay in seconds between requests (default: 1.0)
            max_retries: Maximum number of retry attempts for failed requests (default: 3)
        """
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self._last_request_time: float = 0.0

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the scraper.
        
        Returns:
            str: Unique identifier for this scraper
        """
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Return the base URL for this scraper.
        
        Returns:
            str: Base URL to scrape from
        """
        pass

    async def fetch(self, url: str) -> str | None:
        """Fetch content from a URL with rate limiting and retry logic.
        
        Implements exponential backoff retry strategy and respects rate limiting.
        Logs errors but returns None on failure (graceful degradation).
        
        Args:
            url: URL to fetch
            
        Returns:
            str: Response text on success, None on failure
        """
        for attempt in range(self.max_retries):
            try:
                # Apply rate limiting
                await self._apply_rate_limit()

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                }
                async with httpx.AsyncClient(timeout=10.0, headers=headers, follow_redirects=True) as client:
                    logger.debug(f"[{self.name}] Fetching: {url} (attempt {attempt + 1}/{self.max_retries})")
                    response = await client.get(url)
                    response.raise_for_status()
                    logger.debug(f"[{self.name}] Successfully fetched: {url}")
                    return response.text

            except httpx.HTTPStatusError as e:
                logger.warning(
                    f"[{self.name}] HTTP error {e.response.status_code} for {url} "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                if attempt < self.max_retries - 1:
                    await self._exponential_backoff(attempt)

            except httpx.RequestError as e:
                logger.warning(
                    f"[{self.name}] Request error for {url}: {str(e)} "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                if attempt < self.max_retries - 1:
                    await self._exponential_backoff(attempt)

            except Exception as e:
                logger.error(
                    f"[{self.name}] Unexpected error fetching {url}: {str(e)} "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                if attempt < self.max_retries - 1:
                    await self._exponential_backoff(attempt)

        logger.error(f"[{self.name}] Failed to fetch {url} after {self.max_retries} attempts")
        return None

    @abstractmethod
    async def parse(self, response: str) -> List[Dict[str, Any]]:
        """Parse response content into scholarship data.
        
        Args:
            response: Response text from fetch()
            
        Returns:
            List[Dict[str, Any]]: List of scholarship dictionaries
        """
        pass

    async def scrape(self) -> List[Dict[str, Any]]:
        """Orchestrate the scraping process.
        
        Fetches content from base_url and parses it into scholarship data.
        Returns empty list on failure (graceful degradation).
        
        Returns:
            List[Dict[str, Any]]: List of scholarship dictionaries
        """
        try:
            logger.info(f"[{self.name}] Starting scrape from {self.base_url}")
            response = await self.fetch(self.base_url)

            if response is None:
                logger.warning(f"[{self.name}] No response received, returning empty list")
                return []

            scholarships = await self.parse(response)
            logger.info(f"[{self.name}] Successfully scraped {len(scholarships)} scholarships")
            return scholarships

        except Exception as e:
            logger.error(f"[{self.name}] Scraping failed: {str(e)}")
            return []

    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting delay between requests."""
        import time

        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time

        if time_since_last_request < self.rate_limit_delay:
            delay = self.rate_limit_delay - time_since_last_request
            logger.debug(f"[{self.name}] Rate limiting: waiting {delay:.2f}s")
            await asyncio.sleep(delay)

        self._last_request_time = time.time()

    async def _exponential_backoff(self, attempt: int) -> None:
        """Apply exponential backoff delay before retry.
        
        Args:
            attempt: Current attempt number (0-indexed)
        """
        delay = 2 ** attempt  # 1s, 2s, 4s, etc.
        logger.debug(f"[{self.name}] Exponential backoff: waiting {delay}s before retry")
        await asyncio.sleep(delay)
