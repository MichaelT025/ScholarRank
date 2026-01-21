"""Cross-source deduplication for scholarship records.

Detects duplicate scholarships that appear on multiple sources,
keeping the most complete version and marking others as duplicates.
"""

import hashlib
import logging
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class Deduplicator:
    """Detects and handles duplicate scholarships across sources."""
    
    # Similarity threshold for fuzzy title matching
    TITLE_SIMILARITY_THRESHOLD = 0.85
    
    # Fields to consider when calculating completeness
    COMPLETENESS_FIELDS = [
        'title', 'description', 'amount_min', 'amount_max', 'deadline',
        'application_url', 'raw_eligibility', 'parsed_eligibility',
    ]
    
    def __init__(self, similarity_threshold: float = 0.85):
        """Initialize deduplicator.
        
        Args:
            similarity_threshold: Minimum similarity ratio for title matching (0.0-1.0)
        """
        self.similarity_threshold = similarity_threshold
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison.
        
        Args:
            title: Raw title string
            
        Returns:
            Normalized title (lowercase, no extra whitespace, no common suffixes)
        """
        if not title:
            return ""
        
        # Lowercase
        normalized = title.lower().strip()
        
        # Remove common suffixes
        suffixes = [
            'scholarship', 'scholarships', 'grant', 'grants',
            'award', 'awards', 'fellowship', 'fellowships',
            'program', 'fund', 'foundation',
        ]
        for suffix in suffixes:
            if normalized.endswith(f' {suffix}'):
                normalized = normalized[:-len(suffix)-1].strip()
        
        # Remove special characters
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Collapse whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _title_fingerprint(self, title: str) -> str:
        """Generate fingerprint for quick duplicate detection.
        
        Args:
            title: Raw title string
            
        Returns:
            MD5 hash of normalized title
        """
        normalized = self._normalize_title(title)
        return hashlib.md5(normalized.encode()).hexdigest()[:12]
    
    def _title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity ratio between two titles.
        
        Args:
            title1: First title
            title2: Second title
            
        Returns:
            Similarity ratio (0.0-1.0)
        """
        norm1 = self._normalize_title(title1)
        norm2 = self._normalize_title(title2)
        
        if not norm1 or not norm2:
            return 0.0
        
        # Exact match after normalization
        if norm1 == norm2:
            return 1.0
        
        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def _calculate_completeness(self, scholarship: Dict[str, Any]) -> int:
        """Calculate completeness score for a scholarship.
        
        Args:
            scholarship: Scholarship dictionary
            
        Returns:
            Completeness score (higher = more complete)
        """
        score = 0
        
        for field in self.COMPLETENESS_FIELDS:
            value = scholarship.get(field)
            if value:
                if isinstance(value, str):
                    # Longer text = more complete
                    score += min(len(value), 500) // 50 + 1
                elif isinstance(value, dict):
                    # More fields = more complete
                    score += len(value) * 2
                else:
                    score += 1
        
        # Bonus for having parsed eligibility
        if scholarship.get('parsed_eligibility'):
            score += 10
        
        # Bonus for having deadline
        if scholarship.get('deadline'):
            score += 5
        
        # Bonus for having amount
        if scholarship.get('amount_min') or scholarship.get('amount_max'):
            score += 5
        
        return score
    
    def find_duplicates(
        self, 
        scholarships: List[Dict[str, Any]]
    ) -> List[Tuple[int, int, float]]:
        """Find duplicate pairs in a list of scholarships.
        
        Args:
            scholarships: List of scholarship dictionaries
            
        Returns:
            List of tuples (index1, index2, similarity) for duplicate pairs
        """
        duplicates = []
        n = len(scholarships)
        
        # Build fingerprint index for quick lookups
        fingerprints: Dict[str, List[int]] = {}
        for i, s in enumerate(scholarships):
            title = s.get('title', '')
            fp = self._title_fingerprint(title)
            if fp not in fingerprints:
                fingerprints[fp] = []
            fingerprints[fp].append(i)
        
        # Check exact fingerprint matches first
        for fp, indices in fingerprints.items():
            if len(indices) > 1:
                for i in range(len(indices)):
                    for j in range(i + 1, len(indices)):
                        idx1, idx2 = indices[i], indices[j]
                        title1 = scholarships[idx1].get('title', '')
                        title2 = scholarships[idx2].get('title', '')
                        sim = self._title_similarity(title1, title2)
                        if sim >= self.similarity_threshold:
                            duplicates.append((idx1, idx2, sim))
        
        # For fuzzy matching, we need to compare across fingerprint groups
        # This is O(n^2) but we limit to first 1000 for performance
        if n <= 1000:
            checked: Set[Tuple[int, int]] = set()
            for pair in duplicates:
                checked.add((pair[0], pair[1]))
                checked.add((pair[1], pair[0]))
            
            for i in range(n):
                for j in range(i + 1, n):
                    if (i, j) in checked:
                        continue
                    
                    title1 = scholarships[i].get('title', '')
                    title2 = scholarships[j].get('title', '')
                    
                    # Skip if titles are very different lengths
                    if title1 and title2:
                        len_ratio = min(len(title1), len(title2)) / max(len(title1), len(title2))
                        if len_ratio < 0.5:
                            continue
                    
                    sim = self._title_similarity(title1, title2)
                    if sim >= self.similarity_threshold:
                        duplicates.append((i, j, sim))
        
        logger.info(f"Found {len(duplicates)} duplicate pairs among {n} scholarships")
        return duplicates
    
    def deduplicate(
        self, 
        scholarships: List[Dict[str, Any]],
        mark_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Deduplicate scholarships, keeping the most complete version.
        
        Args:
            scholarships: List of scholarship dictionaries
            mark_only: If True, mark duplicates instead of removing them
            
        Returns:
            Deduplicated list with 'is_duplicate' and 'duplicate_of' fields
        """
        if not scholarships:
            return []
        
        # Calculate completeness for all
        completeness = [self._calculate_completeness(s) for s in scholarships]
        
        # Find duplicates
        duplicate_pairs = self.find_duplicates(scholarships)
        
        # Build a union-find structure to group duplicates
        parent = list(range(len(scholarships)))
        
        def find(x: int) -> int:
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x: int, y: int) -> None:
            px, py = find(x), find(y)
            if px != py:
                # Make the more complete one the parent
                if completeness[px] >= completeness[py]:
                    parent[py] = px
                else:
                    parent[px] = py
        
        # Union duplicate pairs
        for idx1, idx2, _ in duplicate_pairs:
            union(idx1, idx2)
        
        # Mark duplicates
        result = []
        for i, scholarship in enumerate(scholarships):
            s = scholarship.copy()
            root = find(i)
            
            if root != i:
                # This is a duplicate
                s['is_duplicate'] = True
                s['duplicate_of'] = scholarships[root].get('id') or scholarships[root].get('title')
            else:
                s['is_duplicate'] = False
                s['duplicate_of'] = None
            
            if mark_only or not s['is_duplicate']:
                result.append(s)
        
        unique_count = sum(1 for s in result if not s.get('is_duplicate'))
        dup_count = sum(1 for s in result if s.get('is_duplicate'))
        logger.info(f"Deduplication: {unique_count} unique, {dup_count} duplicates marked")
        
        return result
    
    def get_duplicate_groups(
        self, 
        scholarships: List[Dict[str, Any]]
    ) -> List[List[int]]:
        """Group scholarships by duplicates.
        
        Args:
            scholarships: List of scholarship dictionaries
            
        Returns:
            List of groups, each group is a list of indices
        """
        duplicate_pairs = self.find_duplicates(scholarships)
        
        # Build adjacency list
        adj: Dict[int, Set[int]] = {i: set() for i in range(len(scholarships))}
        for idx1, idx2, _ in duplicate_pairs:
            adj[idx1].add(idx2)
            adj[idx2].add(idx1)
        
        # Find connected components
        visited = set()
        groups = []
        
        for i in range(len(scholarships)):
            if i in visited:
                continue
            
            # BFS to find connected component
            group = []
            queue = [i]
            while queue:
                node = queue.pop(0)
                if node in visited:
                    continue
                visited.add(node)
                group.append(node)
                for neighbor in adj[node]:
                    if neighbor not in visited:
                        queue.append(neighbor)
            
            if len(group) > 1:
                groups.append(sorted(group))
        
        return groups
