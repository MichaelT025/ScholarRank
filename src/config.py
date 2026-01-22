"""Configuration management for ScholarRank."""

from pathlib import Path
from typing import Optional

import yaml

from src.profile.models import UserProfile

# Default paths
DATA_DIR = Path(__file__).parent.parent / "data"
DEFAULT_PROFILE_PATH = DATA_DIR / "profile.yaml"
INTERVIEW_DRAFT_PATH = DATA_DIR / "interview_draft.json"
PROFILE_DRAFT_PATH = DATA_DIR / "profile_draft.yaml"
DEFAULT_MATCHES_PATH = DATA_DIR / "matches.csv"


def ensure_data_dir() -> None:
    """Ensure the data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_profile(path: Optional[Path] = None) -> UserProfile:
    """Load user profile from YAML file.

    Args:
        path: Optional path to profile file. Defaults to data/profile.yaml.

    Returns:
        UserProfile instance. Returns empty profile if file doesn't exist.
    """
    if path is None:
        path = DEFAULT_PROFILE_PATH

    if not path.exists():
        return UserProfile()

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        return UserProfile()

    return UserProfile.model_validate(data)


def save_profile(profile: UserProfile, path: Optional[Path] = None) -> Path:
    """Save user profile to YAML file.

    Args:
        profile: UserProfile instance to save.
        path: Optional path to save to. Defaults to data/profile.yaml.

    Returns:
        Path where profile was saved.
    """
    if path is None:
        path = DEFAULT_PROFILE_PATH

    ensure_data_dir()

    # Convert to dict, excluding None values for cleaner YAML
    data = profile.model_dump(mode="json", exclude_none=True)

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    return path


def profile_exists(path: Optional[Path] = None) -> bool:
    """Check if a profile file exists.

    Args:
        path: Optional path to check. Defaults to data/profile.yaml.

    Returns:
        True if profile file exists.
    """
    if path is None:
        path = DEFAULT_PROFILE_PATH

    return path.exists()


def delete_profile(path: Optional[Path] = None) -> bool:
    """Delete the profile file.

    Args:
        path: Optional path to delete. Defaults to data/profile.yaml.

    Returns:
        True if file was deleted, False if it didn't exist.
    """
    if path is None:
        path = DEFAULT_PROFILE_PATH

    if path.exists():
        path.unlink()
        return True
    return False
