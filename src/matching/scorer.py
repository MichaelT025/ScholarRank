"""Fit score calculation for scholarship ranking.

Implements the fit score formula from PRD:
- criteria_match_pct * 0.35
- deadline_urgency * 0.20
- value_density * 0.25
- competition_factor * 0.20
"""

import logging
import math
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from src.matching.matcher import MatchResult

logger = logging.getLogger(__name__)


@dataclass
class FitScore:
    """Complete fit score with breakdown."""
    total: float                 # Overall fit score (0.0-1.0)
    criteria_match: float        # Match percentage component
    deadline_urgency: float      # Deadline urgency component
    value_density: float         # Value/effort ratio component
    competition_factor: float    # Competition estimate component
    
    # Raw values before weighting
    match_percentage: float
    days_until_deadline: Optional[int]
    amount: Optional[int]         # In cents
    effort_score: Optional[int]
    competition_score: Optional[int]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": round(self.total, 3),
            "breakdown": {
                "criteria_match": round(self.criteria_match, 3),
                "deadline_urgency": round(self.deadline_urgency, 3),
                "value_density": round(self.value_density, 3),
                "competition_factor": round(self.competition_factor, 3),
            },
            "raw_values": {
                "match_percentage": round(self.match_percentage, 1),
                "days_until_deadline": self.days_until_deadline,
                "amount_cents": self.amount,
                "effort_score": self.effort_score,
                "competition_score": self.competition_score,
            }
        }
    
    @property
    def total_percentage(self) -> int:
        """Return total as percentage (0-100)."""
        return int(round(self.total * 100))


class FitScorer:
    """Calculates fit scores for scholarships."""
    
    # Weights for each component (must sum to 1.0)
    WEIGHT_CRITERIA = 0.35
    WEIGHT_DEADLINE = 0.20
    WEIGHT_VALUE = 0.25
    WEIGHT_COMPETITION = 0.20
    
    # Default values when data is missing
    DEFAULT_EFFORT = 5           # Medium effort (1-10 scale)
    DEFAULT_COMPETITION = 5      # Medium competition (1-10 scale)
    
    # Deadline urgency parameters
    DEADLINE_HALF_LIFE_DAYS = 30  # Days at which urgency is 0.5
    
    def __init__(self):
        """Initialize the scorer."""
        pass
    
    def calculate(
        self,
        match_result: MatchResult,
        scholarship: Dict[str, Any],
        reference_date: Optional[date] = None
    ) -> FitScore:
        """Calculate fit score for a matched scholarship.
        
        Args:
            match_result: Result from eligibility matching
            scholarship: Scholarship data dictionary
            reference_date: Date to calculate deadline from (default: today)
            
        Returns:
            FitScore with detailed breakdown
        """
        if reference_date is None:
            reference_date = date.today()
        
        # Extract data
        match_pct = match_result.match_percentage
        deadline = self._parse_deadline(scholarship.get("deadline"))
        amount = scholarship.get("amount_max") or scholarship.get("amount_min")
        effort = scholarship.get("effort_score")
        competition = scholarship.get("competition_score")
        
        # Calculate days until deadline
        days_until = None
        if deadline:
            days_until = (deadline - reference_date).days
        
        # Calculate each component
        criteria_score = self._calculate_criteria_match(match_pct)
        deadline_score = self._calculate_deadline_urgency(days_until)
        value_score = self._calculate_value_density(amount, effort)
        competition_score = self._calculate_competition_factor(competition)
        
        # Calculate weighted total
        total = (
            criteria_score * self.WEIGHT_CRITERIA +
            deadline_score * self.WEIGHT_DEADLINE +
            value_score * self.WEIGHT_VALUE +
            competition_score * self.WEIGHT_COMPETITION
        )
        
        return FitScore(
            total=total,
            criteria_match=criteria_score * self.WEIGHT_CRITERIA,
            deadline_urgency=deadline_score * self.WEIGHT_DEADLINE,
            value_density=value_score * self.WEIGHT_VALUE,
            competition_factor=competition_score * self.WEIGHT_COMPETITION,
            match_percentage=match_pct,
            days_until_deadline=days_until,
            amount=amount,
            effort_score=effort,
            competition_score=competition,
        )
    
    def _parse_deadline(self, deadline_value: Any) -> Optional[date]:
        """Parse deadline from various formats."""
        if deadline_value is None:
            return None
        
        if isinstance(deadline_value, date):
            return deadline_value
        
        if isinstance(deadline_value, datetime):
            return deadline_value.date()
        
        if isinstance(deadline_value, str):
            # Try ISO format first
            try:
                return date.fromisoformat(deadline_value)
            except ValueError:
                pass
            
            # Try datetime format
            try:
                return datetime.strptime(deadline_value, "%Y-%m-%d").date()
            except ValueError:
                pass
        
        return None
    
    def _calculate_criteria_match(self, match_percentage: float) -> float:
        """Calculate criteria match score (0-1).
        
        Args:
            match_percentage: Percentage of requirements matched (0-100)
            
        Returns:
            Score from 0 to 1
        """
        # Simple linear scaling from percentage
        return min(1.0, max(0.0, match_percentage / 100.0))
    
    def _calculate_deadline_urgency(self, days_until: Optional[int]) -> float:
        """Calculate deadline urgency using exponential decay.
        
        Closer deadlines = higher urgency = higher score.
        Uses exponential decay so urgency increases rapidly as deadline approaches.
        
        Args:
            days_until: Days until deadline (negative = expired)
            
        Returns:
            Urgency score from 0 to 1
        """
        if days_until is None:
            # No deadline = moderate urgency
            return 0.5
        
        if days_until < 0:
            # Expired = no urgency (won't show anyway)
            return 0.0
        
        if days_until == 0:
            # Due today = maximum urgency
            return 1.0
        
        # Exponential decay: urgency = e^(-days / half_life)
        # At half_life days, urgency = 0.5
        # At 2*half_life days, urgency = 0.25
        decay_rate = math.log(2) / self.DEADLINE_HALF_LIFE_DAYS
        urgency = math.exp(-decay_rate * days_until)
        
        return min(1.0, max(0.0, urgency))
    
    def _calculate_value_density(
        self, 
        amount_cents: Optional[int], 
        effort_score: Optional[int]
    ) -> float:
        """Calculate value density (amount per unit effort).
        
        Higher amount and lower effort = higher score.
        
        Args:
            amount_cents: Award amount in cents
            effort_score: Effort required (1-10, 10 = most effort)
            
        Returns:
            Value density score from 0 to 1
        """
        if amount_cents is None:
            # Unknown amount = assume moderate value
            return 0.5
        
        effort = effort_score if effort_score else self.DEFAULT_EFFORT
        
        # Convert cents to dollars
        amount_dollars = amount_cents / 100
        
        # Calculate value density
        # Use log scale for amount to handle wide range ($100 to $100,000)
        # Effort is on 1-10 scale, invert so lower effort = higher score
        if amount_dollars <= 0:
            return 0.0
        
        log_amount = math.log10(amount_dollars)
        effort_factor = (11 - effort) / 10  # 1 effort -> 1.0, 10 effort -> 0.1
        
        # Normalize: $1000 with effort 5 = ~0.5
        # log10(1000) = 3, effort_factor for 5 = 0.6
        # raw_value = 3 * 0.6 = 1.8
        raw_value = log_amount * effort_factor
        
        # Scale to 0-1 range
        # $100 (log=2) low effort (0.9) = 1.8 -> ~0.4
        # $10000 (log=4) low effort (0.9) = 3.6 -> ~0.8
        # $50000 (log=4.7) low effort (0.9) = 4.23 -> ~0.95
        normalized = raw_value / 4.5  # Normalize so ~$50k low effort = ~1.0
        
        return min(1.0, max(0.0, normalized))
    
    def _calculate_competition_factor(
        self, 
        competition_score: Optional[int]
    ) -> float:
        """Calculate competition factor.
        
        Lower competition = higher score (easier to win).
        
        Args:
            competition_score: Competition level (1-10, 10 = most competitive)
            
        Returns:
            Competition factor score from 0 to 1
        """
        if competition_score is None:
            # Unknown competition = assume moderate
            return 0.5
        
        # Invert: low competition (1) = 1.0, high competition (10) = 0.1
        return (11 - competition_score) / 10
    
    def score_batch(
        self,
        match_results: List[MatchResult],
        scholarships: List[Dict[str, Any]],
        reference_date: Optional[date] = None
    ) -> List[FitScore]:
        """Calculate fit scores for multiple scholarships.
        
        Args:
            match_results: List of MatchResults (same order as scholarships)
            scholarships: List of scholarship dictionaries
            reference_date: Date to calculate deadlines from
            
        Returns:
            List of FitScores (same order)
        """
        if len(match_results) != len(scholarships):
            raise ValueError("match_results and scholarships must have same length")
        
        scores = []
        for match, scholarship in zip(match_results, scholarships):
            score = self.calculate(match, scholarship, reference_date)
            scores.append(score)
        
        logger.info(f"Calculated {len(scores)} fit scores")
        return scores
    
    def rank_scholarships(
        self,
        scholarships: List[Dict[str, Any]],
        scores: List[FitScore],
        eligible_only: bool = True,
        match_results: Optional[List[MatchResult]] = None
    ) -> List[Dict[str, Any]]:
        """Rank scholarships by fit score.
        
        Args:
            scholarships: List of scholarship dictionaries
            scores: List of FitScores (same order)
            eligible_only: Only include eligible scholarships
            match_results: Optional match results for eligibility filtering
            
        Returns:
            Scholarships sorted by fit score (highest first), with score attached
        """
        combined = []
        
        for i, (scholarship, score) in enumerate(zip(scholarships, scores)):
            # Check eligibility if requested
            if eligible_only and match_results:
                if not match_results[i].eligible:
                    continue
            
            # Create copy with score attached
            ranked = scholarship.copy()
            ranked["fit_score"] = score.total
            ranked["fit_score_breakdown"] = score.to_dict()
            if match_results and i < len(match_results):
                ranked["match_result"] = match_results[i].to_dict()
            
            combined.append(ranked)
        
        # Sort by fit score (descending)
        combined.sort(key=lambda x: x["fit_score"], reverse=True)
        
        # Add rank
        for i, scholarship in enumerate(combined, 1):
            scholarship["rank"] = i
        
        logger.info(f"Ranked {len(combined)} scholarships by fit score")
        return combined
