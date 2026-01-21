"""Data normalization for scholarship records.

Standardizes field names, date formats, and amount representations
across different sources to enable consistent matching and display.
"""

import logging
import re
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class Normalizer:
    """Normalizes scholarship data from various sources to a consistent format."""
    
    # Common date formats from different sources
    DATE_FORMATS = [
        "%Y-%m-%d",           # ISO format
        "%m/%d/%Y",           # US format
        "%m/%d/%y",           # US short year
        "%B %d, %Y",          # January 15, 2026
        "%B %d %Y",           # January 15 2026
        "%b %d, %Y",          # Jan 15, 2026
        "%b %d %Y",           # Jan 15 2026
        "%d %B %Y",           # 15 January 2026
        "%d %b %Y",           # 15 Jan 2026
        "%Y/%m/%d",           # ISO with slashes
        "%m-%d-%Y",           # US with dashes
    ]
    
    def normalize_date(self, date_str: Optional[str]) -> Optional[str]:
        """Convert various date formats to ISO format (YYYY-MM-DD).
        
        Args:
            date_str: Date string in any common format
            
        Returns:
            ISO formatted date string or None if parsing fails
        """
        if not date_str:
            return None
        
        # Clean up the string
        date_str = date_str.strip()
        
        # Remove common suffixes like "st", "nd", "rd", "th"
        date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
        
        # Try each format
        for fmt in self.DATE_FORMATS:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        # Try to extract date components with regex
        # Match patterns like "February 15, 2026" or "15 Feb 2026"
        month_names = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        # Try "Month Day, Year" pattern
        match = re.search(
            r'(\w+)\s+(\d{1,2}),?\s+(\d{4})',
            date_str,
            re.IGNORECASE
        )
        if match:
            month_str, day, year = match.groups()
            month = month_names.get(month_str.lower())
            if month:
                try:
                    return date(int(year), month, int(day)).isoformat()
                except ValueError:
                    pass
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def normalize_amount(self, amount_str: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
        """Convert amount string to cents (min, max).
        
        Handles formats like:
        - "$5,000"
        - "$1,000 - $5,000"
        - "Up to $10,000"
        - "Varies"
        - "$500/month"
        
        Args:
            amount_str: Amount string in various formats
            
        Returns:
            Tuple of (min_cents, max_cents), either may be None
        """
        if not amount_str:
            return None, None
        
        amount_str = amount_str.strip().lower()
        
        # Handle "varies" or "variable"
        if 'varies' in amount_str or 'variable' in amount_str:
            return None, None
        
        # Find all dollar amounts in the string
        amounts = re.findall(r'\$[\d,]+(?:\.\d{2})?', amount_str)
        
        if not amounts:
            # Try without dollar sign
            amounts = re.findall(r'[\d,]+(?:\.\d{2})?', amount_str)
        
        if not amounts:
            return None, None
        
        # Parse amounts to cents
        parsed = []
        for amt in amounts:
            # Remove $ and commas
            clean = amt.replace('$', '').replace(',', '')
            try:
                # Convert to cents
                if '.' in clean:
                    dollars = float(clean)
                else:
                    dollars = int(clean)
                parsed.append(int(dollars * 100))
            except ValueError:
                continue
        
        if not parsed:
            return None, None
        
        if len(parsed) == 1:
            amount = parsed[0]
            # Handle "up to" case
            if 'up to' in amount_str or 'maximum' in amount_str:
                return None, amount
            return amount, amount
        
        # Range case
        return min(parsed), max(parsed)
    
    def normalize_source_name(self, source: str) -> str:
        """Standardize source names.
        
        Args:
            source: Raw source name
            
        Returns:
            Standardized source name
        """
        source_map = {
            "scholarships_com": "scholarships.com",
            "scholarships.com": "scholarships.com",
            "fastweb": "fastweb",
            "careeronestop": "careeronestop",
            "CareerOneStop": "careeronestop",
            "iefa": "iefa",
            "IEFA": "iefa",
            "intl_scholarships_com": "internationalscholarships.com",
            "intl_scholarships": "internationalscholarships.com",
            "internationalscholarships.com": "internationalscholarships.com",
            "scholars4dev": "scholars4dev",
        }
        return source_map.get(source, source.lower())
    
    def normalize_scholarship(self, scholarship: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a single scholarship record.
        
        Args:
            scholarship: Raw scholarship dictionary
            
        Returns:
            Normalized scholarship dictionary
        """
        normalized = scholarship.copy()
        
        # Normalize source
        if 'source' in normalized:
            normalized['source'] = self.normalize_source_name(normalized['source'])
        
        # Normalize deadline
        deadline_raw = normalized.get('deadline')
        if deadline_raw and isinstance(deadline_raw, str):
            normalized['deadline'] = self.normalize_date(deadline_raw)
        
        # Normalize amount
        amount_raw = normalized.get('amount')
        if amount_raw and isinstance(amount_raw, str):
            min_cents, max_cents = self.normalize_amount(amount_raw)
            normalized['amount_min'] = min_cents
            normalized['amount_max'] = max_cents
            # Keep original for reference
            normalized['amount_raw'] = amount_raw
        
        # Ensure title is cleaned
        if 'title' in normalized and normalized['title']:
            normalized['title'] = normalized['title'].strip()
        
        # Ensure URL is absolute
        if 'url' in normalized and normalized['url']:
            url = normalized['url']
            if url.startswith('//'):
                normalized['url'] = 'https:' + url
        
        return normalized
    
    def normalize_batch(self, scholarships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize a batch of scholarships.
        
        Args:
            scholarships: List of raw scholarship dictionaries
            
        Returns:
            List of normalized scholarship dictionaries
        """
        normalized = []
        for s in scholarships:
            try:
                normalized.append(self.normalize_scholarship(s))
            except Exception as e:
                logger.warning(f"Failed to normalize scholarship: {e}")
                normalized.append(s)  # Keep original on failure
        
        logger.info(f"Normalized {len(normalized)} scholarships")
        return normalized
