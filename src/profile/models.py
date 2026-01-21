"""Pydantic models for user profile data."""

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CitizenshipStatus(str, Enum):
    """Citizenship/residency status options."""

    US_CITIZEN = "us_citizen"
    PERMANENT_RESIDENT = "permanent_resident"
    INTERNATIONAL = "international"
    DACA = "daca"
    REFUGEE = "refugee"
    OTHER = "other"


class DegreeLevel(str, Enum):
    """Academic degree level."""

    HIGH_SCHOOL = "high_school"
    UNDERGRADUATE = "undergraduate"
    GRADUATE = "graduate"
    DOCTORAL = "doctoral"
    PROFESSIONAL = "professional"


class YearInSchool(str, Enum):
    """Year in school for undergraduates."""

    FRESHMAN = "freshman"
    SOPHOMORE = "sophomore"
    JUNIOR = "junior"
    SENIOR = "senior"
    FIFTH_YEAR = "fifth_year"
    GRADUATE_1 = "graduate_1"
    GRADUATE_2 = "graduate_2"
    GRADUATE_3_PLUS = "graduate_3_plus"


class Gender(str, Enum):
    """Gender options."""

    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non_binary"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class AcademicInfo(BaseModel):
    """Academic information."""

    gpa: Optional[float] = Field(None, ge=0.0, le=4.0, description="GPA on 4.0 scale")
    major: Optional[str] = Field(None, description="Primary major")
    minor: Optional[str] = Field(None, description="Minor if any")
    degree_level: Optional[DegreeLevel] = Field(None, description="Current degree level")
    year_in_school: Optional[YearInSchool] = Field(None, description="Year in school")
    institution: Optional[str] = Field(None, description="Name of institution")
    institution_type: Optional[str] = Field(
        None, description="Type: community_college, 4year_public, 4year_private, etc."
    )
    expected_graduation: Optional[date] = Field(None, description="Expected graduation date")
    enrolled: Optional[bool] = Field(None, description="Currently enrolled")


class LocationInfo(BaseModel):
    """Location and residency information."""

    country_of_origin: Optional[str] = Field(None, description="Country of origin")
    country_of_residence: Optional[str] = Field(None, description="Current country of residence")
    state: Optional[str] = Field(None, description="US state if applicable")
    city: Optional[str] = Field(None, description="City")
    citizenship_status: Optional[CitizenshipStatus] = Field(None, description="Citizenship status")
    destination_country: Optional[str] = Field(
        "USA", description="Country where studying (default USA)"
    )


class DemographicInfo(BaseModel):
    """Demographic information."""

    gender: Optional[Gender] = Field(None, description="Gender")
    ethnicity: Optional[list[str]] = Field(
        default_factory=list,
        description="Ethnicity/race (can be multiple)",
    )
    first_generation: Optional[bool] = Field(
        None, description="First generation college student"
    )
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    veteran: Optional[bool] = Field(None, description="Veteran status")
    disability: Optional[bool] = Field(None, description="Has disability")
    lgbtq: Optional[bool] = Field(None, description="LGBTQ+ identity")


class FinancialInfo(BaseModel):
    """Financial information."""

    household_income: Optional[str] = Field(
        None,
        description="Income bracket: under_30k, 30k_60k, 60k_100k, 100k_150k, over_150k",
    )
    financial_need: Optional[bool] = Field(None, description="Demonstrates financial need")
    fafsa_efc: Optional[int] = Field(
        None, ge=0, description="Expected Family Contribution from FAFSA"
    )
    pell_eligible: Optional[bool] = Field(None, description="Pell Grant eligible")
    employed: Optional[bool] = Field(None, description="Currently employed")
    work_study: Optional[bool] = Field(None, description="In work-study program")


class InterestsInfo(BaseModel):
    """Interests, activities, and career goals."""

    career_goals: Optional[list[str]] = Field(
        default_factory=list, description="Career goals/interests"
    )
    hobbies: Optional[list[str]] = Field(default_factory=list, description="Hobbies")
    activities: Optional[list[str]] = Field(
        default_factory=list, description="Extracurricular activities"
    )
    volunteer_work: Optional[list[str]] = Field(
        default_factory=list, description="Volunteer/community service"
    )
    leadership_roles: Optional[list[str]] = Field(
        default_factory=list, description="Leadership positions held"
    )
    sports: Optional[list[str]] = Field(default_factory=list, description="Sports played")
    arts: Optional[list[str]] = Field(
        default_factory=list, description="Arts involvement (music, theater, etc.)"
    )


class AffiliationsInfo(BaseModel):
    """Affiliations and memberships."""

    organizations: Optional[list[str]] = Field(
        default_factory=list, description="Organization memberships"
    )
    clubs: Optional[list[str]] = Field(default_factory=list, description="Club memberships")
    religious_affiliation: Optional[str] = Field(None, description="Religious affiliation")
    military_affiliation: Optional[str] = Field(
        None, description="Military branch/status if applicable"
    )
    union_membership: Optional[str] = Field(None, description="Union membership")
    employer: Optional[str] = Field(None, description="Current/past employer for employer scholarships")


class UserProfile(BaseModel):
    """Complete user profile for scholarship matching."""

    # Profile metadata
    name: Optional[str] = Field(None, description="User's name")
    email: Optional[str] = Field(None, description="Email address")
    created_at: Optional[date] = Field(default_factory=date.today)
    updated_at: Optional[date] = Field(default_factory=date.today)

    # Profile sections
    academic: AcademicInfo = Field(default_factory=AcademicInfo)
    location: LocationInfo = Field(default_factory=LocationInfo)
    demographics: DemographicInfo = Field(default_factory=DemographicInfo)
    financial: FinancialInfo = Field(default_factory=FinancialInfo)
    interests: InterestsInfo = Field(default_factory=InterestsInfo)
    affiliations: AffiliationsInfo = Field(default_factory=AffiliationsInfo)

    def is_empty(self) -> bool:
        """Check if profile has any meaningful data."""
        # Check if any field in any section has a value
        for section in [
            self.academic,
            self.location,
            self.demographics,
            self.financial,
            self.interests,
            self.affiliations,
        ]:
            for field_name, field_value in section.model_dump().items():
                if field_value is not None:
                    if isinstance(field_value, list) and len(field_value) > 0:
                        return False
                    elif not isinstance(field_value, list):
                        return False
        return True

    def completion_percentage(self) -> float:
        """Calculate profile completion percentage."""
        total_fields = 0
        filled_fields = 0

        for section in [
            self.academic,
            self.location,
            self.demographics,
            self.financial,
            self.interests,
            self.affiliations,
        ]:
            for field_name, field_value in section.model_dump().items():
                total_fields += 1
                if field_value is not None:
                    if isinstance(field_value, list) and len(field_value) > 0:
                        filled_fields += 1
                    elif not isinstance(field_value, list):
                        filled_fields += 1

        return (filled_fields / total_fields * 100) if total_fields > 0 else 0.0

    def get_summary(self) -> dict:
        """Get a summary of key profile attributes for display."""
        return {
            "name": self.name,
            "gpa": self.academic.gpa,
            "major": self.academic.major,
            "year": self.academic.year_in_school.value if self.academic.year_in_school else None,
            "institution": self.academic.institution,
            "citizenship": self.location.citizenship_status.value if self.location.citizenship_status else None,
            "state": self.location.state,
            "first_gen": self.demographics.first_generation,
            "ethnicity": self.demographics.ethnicity,
            "completion": f"{self.completion_percentage():.0f}%",
        }
