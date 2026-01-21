"""LLM-powered eligibility extraction with caching.

Uses OpenAI gpt-4o-mini to parse raw eligibility text into structured JSON.
Implements content-hash based caching to avoid re-processing identical content.
"""

import hashlib
import json
import logging
import os
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ParsedEligibility(BaseModel):
    """Structured eligibility requirements extracted by LLM."""
    
    min_gpa: Optional[float] = Field(None, description="Minimum GPA required (0.0-4.0 scale)")
    max_gpa: Optional[float] = Field(None, description="Maximum GPA if specified")
    majors: List[str] = Field(default_factory=list, description="Required or preferred majors/fields of study")
    degree_levels: List[str] = Field(default_factory=list, description="e.g., undergraduate, graduate, PhD")
    year_in_school: List[str] = Field(default_factory=list, description="e.g., freshman, sophomore, junior, senior")
    citizenship: List[str] = Field(default_factory=list, description="e.g., US Citizen, Permanent Resident, International")
    demographics: List[str] = Field(default_factory=list, description="e.g., Hispanic, First-generation, Female, LGBTQ+")
    states: List[str] = Field(default_factory=list, description="Required states of residence")
    financial_need: Optional[bool] = Field(None, description="Whether financial need is required")
    military_affiliation: Optional[bool] = Field(None, description="Military service or family required")
    disabilities: Optional[bool] = Field(None, description="Disability-related eligibility")
    organizations: List[str] = Field(default_factory=list, description="Required organization memberships")
    other: List[str] = Field(default_factory=list, description="Other requirements not fitting above categories")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in self.model_dump().items() if v is not None and v != []}


# System prompt for eligibility extraction
EXTRACTION_PROMPT = """You are an expert at parsing scholarship eligibility requirements. 
Given raw eligibility text, extract structured information into the specified JSON format.

Rules:
1. Only extract information that is EXPLICITLY stated in the text
2. Do NOT make assumptions or infer requirements
3. If a field is not mentioned, leave it empty/null
4. For GPA, normalize to 4.0 scale if possible
5. For demographics, use standardized terms: Hispanic, Latino, African American, Asian, Native American, First-generation, Female, Male, LGBTQ+, etc.
6. For citizenship, use: US Citizen, Permanent Resident, DACA, International Student, Undocumented
7. List multiple options when the scholarship accepts alternatives

Output ONLY valid JSON matching the schema. No additional text."""


class EligibilityExtractor:
    """Extracts structured eligibility from raw text using LLM with caching."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize extractor with optional cache directory.
        
        Args:
            cache_dir: Directory to store cache files. Defaults to data/cache/
        """
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"
        self.cache_dir = cache_dir or "data/cache"
        self._ensure_cache_dir()
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_cache()
    
    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _cache_file_path(self) -> str:
        """Get path to cache file."""
        return os.path.join(self.cache_dir, "eligibility_cache.json")
    
    def _load_cache(self) -> None:
        """Load cache from disk."""
        cache_path = self._cache_file_path()
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                logger.info(f"Loaded {len(self._cache)} cached extractions")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
                self._cache = {}
    
    def _save_cache(self) -> None:
        """Save cache to disk."""
        cache_path = self._cache_file_path()
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _content_hash(self, text: str) -> str:
        """Generate hash of content for cache key."""
        normalized = text.strip().lower()
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def get_cached(self, text: str) -> Optional[Dict[str, Any]]:
        """Check if extraction exists in cache.
        
        Args:
            text: Raw eligibility text
            
        Returns:
            Cached parsed eligibility or None
        """
        content_hash = self._content_hash(text)
        return self._cache.get(content_hash)
    
    async def extract(self, text: str, use_cache: bool = True) -> Dict[str, Any]:
        """Extract structured eligibility from raw text.
        
        Args:
            text: Raw eligibility text
            use_cache: Whether to use cached results
            
        Returns:
            Parsed eligibility as dictionary
        """
        if not text or not text.strip():
            return {}
        
        # Check cache first
        content_hash = self._content_hash(text)
        if use_cache and content_hash in self._cache:
            logger.debug(f"Cache hit for content hash {content_hash}")
            return self._cache[content_hash]
        
        # Call LLM
        try:
            logger.info(f"Extracting eligibility from {len(text)} chars of text")
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": EXTRACTION_PROMPT},
                    {"role": "user", "content": f"Extract eligibility requirements from:\n\n{text}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=1000,
            )
            
            result_text = response.choices[0].message.content
            if not result_text:
                logger.warning("Empty response from LLM")
                return {}
            
            # Parse and validate
            raw_result = json.loads(result_text)
            
            # Validate with Pydantic model
            parsed = ParsedEligibility(**raw_result)
            result = parsed.to_dict()
            
            # Cache the result
            self._cache[content_hash] = result
            self._save_cache()
            
            logger.info(f"Extracted eligibility with {len(result)} fields")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {}
    
    async def extract_batch(
        self, 
        items: List[Dict[str, Any]], 
        text_field: str = "raw_eligibility",
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Extract eligibility for multiple items.
        
        Args:
            items: List of scholarship dictionaries
            text_field: Field containing raw eligibility text
            use_cache: Whether to use cached results
            
        Returns:
            List of items with 'parsed_eligibility' added
        """
        results = []
        cache_hits = 0
        api_calls = 0
        
        for item in items:
            text = item.get(text_field) or item.get("description") or item.get("requirements") or ""
            
            # Check cache
            cached = self.get_cached(text) if use_cache else None
            
            if cached:
                cache_hits += 1
                item["parsed_eligibility"] = cached
            elif text:
                item["parsed_eligibility"] = await self.extract(text, use_cache=use_cache)
                api_calls += 1
            else:
                item["parsed_eligibility"] = {}
            
            results.append(item)
        
        logger.info(f"Batch extraction complete: {cache_hits} cache hits, {api_calls} API calls")
        return results
    
    def clear_cache(self) -> None:
        """Clear all cached extractions."""
        self._cache = {}
        cache_path = self._cache_file_path()
        if os.path.exists(cache_path):
            os.remove(cache_path)
        logger.info("Cache cleared")
    
    @property
    def cache_size(self) -> int:
        """Return number of cached extractions."""
        return len(self._cache)
