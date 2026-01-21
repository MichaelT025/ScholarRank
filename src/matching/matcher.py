"""Eligibility matching engine.

Compares user profile against scholarship eligibility requirements,
implementing hard filters (must match) and soft filters (should match).
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from src.profile.models import UserProfile, CitizenshipStatus

logger = logging.getLogger(__name__)


class MatchStatus(str, Enum):
    """Status of a requirement match."""
    MATCHED = "matched"      # User meets requirement
    PARTIAL = "partial"      # User partially meets requirement
    UNMATCHED = "unmatched"  # User doesn't meet requirement
    UNKNOWN = "unknown"      # Cannot determine (missing data)
    NOT_APPLICABLE = "n/a"   # Requirement doesn't apply


@dataclass
class RequirementMatch:
    """Result of matching a single requirement."""
    requirement: str           # Description of the requirement
    status: MatchStatus        # Match status
    user_value: Optional[str] = None  # User's value for this field
    required_value: Optional[str] = None  # Required value
    is_hard: bool = True       # Hard requirement (disqualifying if unmatched)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirement": self.requirement,
            "status": self.status.value,
            "user_value": self.user_value,
            "required_value": self.required_value,
            "is_hard": self.is_hard,
        }


@dataclass
class MatchResult:
    """Result of matching a scholarship against a profile."""
    scholarship_id: str
    eligible: bool                          # Overall eligibility
    match_count: int = 0                    # Number of matched requirements
    total_requirements: int = 0             # Total requirements checked
    partial_count: int = 0                  # Number of partial matches
    match_percentage: float = 0.0           # Percentage of requirements met
    details: List[RequirementMatch] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scholarship_id": self.scholarship_id,
            "eligible": self.eligible,
            "match_count": self.match_count,
            "total_requirements": self.total_requirements,
            "partial_count": self.partial_count,
            "match_percentage": self.match_percentage,
            "details": [d.to_dict() for d in self.details],
        }
    
    @property
    def match_summary(self) -> str:
        """Return summary like '4/5' or '3/4 ~'."""
        if self.partial_count > 0:
            return f"{self.match_count}/{self.total_requirements} ~"
        return f"{self.match_count}/{self.total_requirements}"


class EligibilityMatcher:
    """Matches user profiles against scholarship eligibility requirements."""
    
    # Mapping of citizenship status to accepted values
    CITIZENSHIP_MAP = {
        CitizenshipStatus.US_CITIZEN: ["US Citizen", "US Citizens", "American", "Citizen"],
        CitizenshipStatus.PERMANENT_RESIDENT: ["Permanent Resident", "Green Card", "LPR"],
        CitizenshipStatus.INTERNATIONAL: ["International", "International Student", "Foreign"],
        CitizenshipStatus.DACA: ["DACA", "Dreamer"],
        CitizenshipStatus.REFUGEE: ["Refugee", "Asylee"],
    }
    
    def __init__(self):
        """Initialize the matcher."""
        pass
    
    def match(
        self, 
        profile: UserProfile, 
        eligibility: Dict[str, Any],
        scholarship_id: str = ""
    ) -> MatchResult:
        """Match a profile against scholarship eligibility.
        
        Args:
            profile: User profile
            eligibility: Parsed eligibility dictionary
            scholarship_id: ID of the scholarship
            
        Returns:
            MatchResult with details of the match
        """
        details: List[RequirementMatch] = []
        hard_failure = False
        
        # Check GPA (hard requirement)
        gpa_match = self._check_gpa(profile, eligibility)
        if gpa_match:
            details.append(gpa_match)
            if gpa_match.status == MatchStatus.UNMATCHED and gpa_match.is_hard:
                hard_failure = True
        
        # Check citizenship (hard requirement)
        citizenship_match = self._check_citizenship(profile, eligibility)
        if citizenship_match:
            details.append(citizenship_match)
            if citizenship_match.status == MatchStatus.UNMATCHED and citizenship_match.is_hard:
                hard_failure = True
        
        # Check majors (soft requirement)
        major_match = self._check_major(profile, eligibility)
        if major_match:
            details.append(major_match)
        
        # Check degree level (soft requirement)
        degree_match = self._check_degree_level(profile, eligibility)
        if degree_match:
            details.append(degree_match)
        
        # Check year in school (soft requirement)
        year_match = self._check_year(profile, eligibility)
        if year_match:
            details.append(year_match)
        
        # Check demographics (soft requirement)
        demo_matches = self._check_demographics(profile, eligibility)
        details.extend(demo_matches)
        
        # Check state (soft requirement)
        state_match = self._check_state(profile, eligibility)
        if state_match:
            details.append(state_match)
        
        # Check financial need (soft requirement)
        financial_match = self._check_financial_need(profile, eligibility)
        if financial_match:
            details.append(financial_match)
        
        # Check military affiliation (soft requirement)
        military_match = self._check_military(profile, eligibility)
        if military_match:
            details.append(military_match)
        
        # Calculate summary statistics
        matched = sum(1 for d in details if d.status == MatchStatus.MATCHED)
        partial = sum(1 for d in details if d.status == MatchStatus.PARTIAL)
        total = sum(1 for d in details if d.status not in [MatchStatus.UNKNOWN, MatchStatus.NOT_APPLICABLE])
        
        # Calculate match percentage
        if total > 0:
            # Partial matches count as 0.5
            match_score = matched + (partial * 0.5)
            match_percentage = (match_score / total) * 100
        else:
            # No requirements = 100% match
            match_percentage = 100.0
        
        # Determine eligibility
        eligible = not hard_failure
        
        return MatchResult(
            scholarship_id=scholarship_id,
            eligible=eligible,
            match_count=matched,
            total_requirements=total,
            partial_count=partial,
            match_percentage=match_percentage,
            details=details,
        )
    
    def _check_gpa(
        self, 
        profile: UserProfile, 
        eligibility: Dict[str, Any]
    ) -> Optional[RequirementMatch]:
        """Check GPA requirement."""
        min_gpa = eligibility.get("min_gpa")
        if min_gpa is None:
            return None
        
        user_gpa = profile.academic.gpa
        
        if user_gpa is None:
            return RequirementMatch(
                requirement=f"GPA >= {min_gpa}",
                status=MatchStatus.UNKNOWN,
                user_value="Not specified",
                required_value=str(min_gpa),
                is_hard=True,
            )
        
        if user_gpa >= min_gpa:
            return RequirementMatch(
                requirement=f"GPA >= {min_gpa}",
                status=MatchStatus.MATCHED,
                user_value=str(user_gpa),
                required_value=str(min_gpa),
                is_hard=True,
            )
        else:
            return RequirementMatch(
                requirement=f"GPA >= {min_gpa}",
                status=MatchStatus.UNMATCHED,
                user_value=str(user_gpa),
                required_value=str(min_gpa),
                is_hard=True,
            )
    
    def _check_citizenship(
        self, 
        profile: UserProfile, 
        eligibility: Dict[str, Any]
    ) -> Optional[RequirementMatch]:
        """Check citizenship requirement."""
        required_citizenship = eligibility.get("citizenship", [])
        if not required_citizenship:
            return None
        
        user_citizenship = profile.location.citizenship_status
        
        if user_citizenship is None:
            return RequirementMatch(
                requirement=f"Citizenship: {', '.join(required_citizenship)}",
                status=MatchStatus.UNKNOWN,
                user_value="Not specified",
                required_value=", ".join(required_citizenship),
                is_hard=True,
            )
        
        # Check if user's citizenship matches any required value
        user_values = self.CITIZENSHIP_MAP.get(user_citizenship, [user_citizenship.value])
        
        matched = False
        for req in required_citizenship:
            req_lower = req.lower()
            for uv in user_values:
                if uv.lower() in req_lower or req_lower in uv.lower():
                    matched = True
                    break
            if matched:
                break
        
        # Special case: "International" often means NOT US Citizen
        if not matched and user_citizenship == CitizenshipStatus.INTERNATIONAL:
            for req in required_citizenship:
                if "international" in req.lower():
                    matched = True
                    break
        
        return RequirementMatch(
            requirement=f"Citizenship: {', '.join(required_citizenship)}",
            status=MatchStatus.MATCHED if matched else MatchStatus.UNMATCHED,
            user_value=user_citizenship.value if user_citizenship else None,
            required_value=", ".join(required_citizenship),
            is_hard=True,
        )
    
    def _check_major(
        self, 
        profile: UserProfile, 
        eligibility: Dict[str, Any]
    ) -> Optional[RequirementMatch]:
        """Check major requirement."""
        required_majors = eligibility.get("majors", [])
        if not required_majors:
            return None
        
        user_major = profile.academic.major
        
        if not user_major:
            return RequirementMatch(
                requirement=f"Major: {', '.join(required_majors[:3])}...",
                status=MatchStatus.UNKNOWN,
                user_value="Not specified",
                required_value=", ".join(required_majors[:3]),
                is_hard=False,
            )
        
        # Check for match (case-insensitive, partial matching)
        user_major_lower = user_major.lower()
        matched = False
        partial = False
        
        for req in required_majors:
            req_lower = req.lower()
            if req_lower in user_major_lower or user_major_lower in req_lower:
                matched = True
                break
            # Check for related fields (e.g., "STEM" matches "Computer Science")
            if self._is_related_field(user_major_lower, req_lower):
                partial = True
        
        if matched:
            status = MatchStatus.MATCHED
        elif partial:
            status = MatchStatus.PARTIAL
        else:
            status = MatchStatus.UNMATCHED
        
        return RequirementMatch(
            requirement=f"Major: {', '.join(required_majors[:3])}",
            status=status,
            user_value=user_major,
            required_value=", ".join(required_majors[:3]),
            is_hard=False,
        )
    
    def _is_related_field(self, user_field: str, required_field: str) -> bool:
        """Check if fields are related (e.g., STEM includes CS)."""
        stem_fields = ["computer", "engineering", "math", "science", "physics", "chemistry", "biology", "data"]
        business_fields = ["business", "finance", "accounting", "economics", "marketing"]
        arts_fields = ["art", "music", "theater", "film", "design", "creative"]
        
        if required_field in ["stem", "science", "technology", "engineering", "mathematics"]:
            return any(f in user_field for f in stem_fields)
        if required_field in ["business", "commerce"]:
            return any(f in user_field for f in business_fields)
        if required_field in ["arts", "humanities"]:
            return any(f in user_field for f in arts_fields)
        
        return False
    
    def _check_degree_level(
        self, 
        profile: UserProfile, 
        eligibility: Dict[str, Any]
    ) -> Optional[RequirementMatch]:
        """Check degree level requirement."""
        required_levels = eligibility.get("degree_levels", [])
        if not required_levels:
            return None
        
        user_level = profile.academic.degree_level
        
        if not user_level:
            return RequirementMatch(
                requirement=f"Degree: {', '.join(required_levels)}",
                status=MatchStatus.UNKNOWN,
                user_value="Not specified",
                required_value=", ".join(required_levels),
                is_hard=False,
            )
        
        # Check for match
        user_level_str = user_level.value.lower()
        matched = any(
            req.lower() in user_level_str or user_level_str in req.lower()
            for req in required_levels
        )
        
        return RequirementMatch(
            requirement=f"Degree: {', '.join(required_levels)}",
            status=MatchStatus.MATCHED if matched else MatchStatus.UNMATCHED,
            user_value=user_level.value,
            required_value=", ".join(required_levels),
            is_hard=False,
        )
    
    def _check_year(
        self, 
        profile: UserProfile, 
        eligibility: Dict[str, Any]
    ) -> Optional[RequirementMatch]:
        """Check year in school requirement."""
        required_years = eligibility.get("year_in_school", [])
        if not required_years:
            return None
        
        user_year = profile.academic.year_in_school
        
        if not user_year:
            return RequirementMatch(
                requirement=f"Year: {', '.join(required_years)}",
                status=MatchStatus.UNKNOWN,
                user_value="Not specified",
                required_value=", ".join(required_years),
                is_hard=False,
            )
        
        # Check for match
        user_year_str = user_year.value.lower()
        matched = any(
            req.lower() in user_year_str or user_year_str in req.lower()
            for req in required_years
        )
        
        return RequirementMatch(
            requirement=f"Year: {', '.join(required_years)}",
            status=MatchStatus.MATCHED if matched else MatchStatus.UNMATCHED,
            user_value=user_year.value,
            required_value=", ".join(required_years),
            is_hard=False,
        )
    
    def _check_demographics(
        self, 
        profile: UserProfile, 
        eligibility: Dict[str, Any]
    ) -> List[RequirementMatch]:
        """Check demographic requirements."""
        results = []
        required_demographics = eligibility.get("demographics", [])
        
        if not required_demographics:
            return results
        
        user_ethnicity = profile.demographics.ethnicity or []
        user_first_gen = profile.demographics.first_generation
        user_gender = profile.demographics.gender
        user_lgbtq = profile.demographics.lgbtq
        
        for req in required_demographics:
            req_lower = req.lower()
            matched = False
            user_value = None
            
            # Check ethnicity
            if any(e.lower() in req_lower or req_lower in e.lower() for e in user_ethnicity):
                matched = True
                user_value = ", ".join(user_ethnicity)
            
            # Check first-generation
            if "first" in req_lower and "generation" in req_lower:
                if user_first_gen is True:
                    matched = True
                    user_value = "First-generation"
                elif user_first_gen is False:
                    user_value = "Not first-generation"
            
            # Check gender
            if user_gender:
                if user_gender.value.lower() in req_lower or req_lower in user_gender.value.lower():
                    matched = True
                    user_value = user_gender.value
            
            # Check LGBTQ+
            if "lgbtq" in req_lower or "lgbt" in req_lower:
                if user_lgbtq is True:
                    matched = True
                    user_value = "LGBTQ+"
                elif user_lgbtq is False:
                    user_value = "Not LGBTQ+"
            
            if user_value is None:
                status = MatchStatus.UNKNOWN
                user_value = "Not specified"
            elif matched:
                status = MatchStatus.MATCHED
            else:
                status = MatchStatus.UNMATCHED
            
            results.append(RequirementMatch(
                requirement=f"Demographics: {req}",
                status=status,
                user_value=user_value,
                required_value=req,
                is_hard=False,
            ))
        
        return results
    
    def _check_state(
        self, 
        profile: UserProfile, 
        eligibility: Dict[str, Any]
    ) -> Optional[RequirementMatch]:
        """Check state of residence requirement."""
        required_states = eligibility.get("states", [])
        if not required_states:
            return None
        
        user_state = profile.location.state
        
        if not user_state:
            return RequirementMatch(
                requirement=f"State: {', '.join(required_states)}",
                status=MatchStatus.UNKNOWN,
                user_value="Not specified",
                required_value=", ".join(required_states),
                is_hard=False,
            )
        
        # Check for match
        user_state_lower = user_state.lower()
        matched = any(
            req.lower() in user_state_lower or user_state_lower in req.lower()
            for req in required_states
        )
        
        return RequirementMatch(
            requirement=f"State: {', '.join(required_states)}",
            status=MatchStatus.MATCHED if matched else MatchStatus.UNMATCHED,
            user_value=user_state,
            required_value=", ".join(required_states),
            is_hard=False,
        )
    
    def _check_financial_need(
        self, 
        profile: UserProfile, 
        eligibility: Dict[str, Any]
    ) -> Optional[RequirementMatch]:
        """Check financial need requirement."""
        requires_financial_need = eligibility.get("financial_need")
        if requires_financial_need is None:
            return None
        
        user_has_need = profile.financial.financial_need
        
        if user_has_need is None:
            return RequirementMatch(
                requirement="Demonstrates financial need",
                status=MatchStatus.UNKNOWN,
                user_value="Not specified",
                required_value="Yes" if requires_financial_need else "No",
                is_hard=False,
            )
        
        if requires_financial_need and user_has_need:
            status = MatchStatus.MATCHED
        elif not requires_financial_need:
            status = MatchStatus.MATCHED  # Not required, so it's fine
        else:
            status = MatchStatus.UNMATCHED
        
        return RequirementMatch(
            requirement="Demonstrates financial need",
            status=status,
            user_value="Yes" if user_has_need else "No",
            required_value="Yes" if requires_financial_need else "No",
            is_hard=False,
        )
    
    def _check_military(
        self, 
        profile: UserProfile, 
        eligibility: Dict[str, Any]
    ) -> Optional[RequirementMatch]:
        """Check military affiliation requirement."""
        requires_military = eligibility.get("military_affiliation")
        if requires_military is None:
            return None
        
        user_military = profile.affiliations.military_affiliation
        user_veteran = profile.demographics.veteran
        
        has_military = bool(user_military) or (user_veteran is True)
        
        if not user_military and user_veteran is None:
            return RequirementMatch(
                requirement="Military affiliation",
                status=MatchStatus.UNKNOWN,
                user_value="Not specified",
                required_value="Required" if requires_military else "Not required",
                is_hard=False,
            )
        
        if requires_military and has_military:
            status = MatchStatus.MATCHED
        elif not requires_military:
            status = MatchStatus.MATCHED
        else:
            status = MatchStatus.UNMATCHED
        
        return RequirementMatch(
            requirement="Military affiliation",
            status=status,
            user_value=user_military or ("Veteran" if user_veteran else "No"),
            required_value="Required" if requires_military else "Not required",
            is_hard=False,
        )
    
    def match_batch(
        self, 
        profile: UserProfile, 
        scholarships: List[Dict[str, Any]]
    ) -> List[MatchResult]:
        """Match a profile against multiple scholarships.
        
        Args:
            profile: User profile
            scholarships: List of scholarship dictionaries with 'parsed_eligibility'
            
        Returns:
            List of MatchResults
        """
        results = []
        for scholarship in scholarships:
            eligibility = scholarship.get("parsed_eligibility", {})
            scholarship_id = scholarship.get("id", scholarship.get("title", "unknown"))
            result = self.match(profile, eligibility, scholarship_id)
            results.append(result)
        
        logger.info(f"Matched {len(results)} scholarships, {sum(1 for r in results if r.eligible)} eligible")
        return results
