"""Export functions for scholarship data in multiple formats."""

import csv
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def _format_amount(cents: Optional[int]) -> str:
    """Format amount in cents to dollar string."""
    if cents is None:
        return "Varies"
    return f"${cents // 100:,}"


def _get_profile_hash(scholarships: List[Dict[str, Any]]) -> str:
    """Generate a hash representing the profile used for matching.
    
    Uses the first scholarship's match_result to infer profile characteristics.
    """
    if not scholarships:
        return "unknown"
    
    # Create a simple hash from the first match result
    first = scholarships[0]
    match_result = first.get("match_result", {})
    details = match_result.get("details", [])
    
    # Hash the requirement types to create a profile signature
    req_types = sorted([d.get("requirement", "") for d in details])
    profile_str = "|".join(req_types)
    
    return hashlib.md5(profile_str.encode()).hexdigest()[:8]


def export_json(
    scholarships: List[Dict[str, Any]],
    filepath: str,
) -> None:
    """Export scholarships to JSON format.
    
    Args:
        scholarships: List of scholarship dictionaries with match results
        filepath: Path to write JSON file
        
    Raises:
        IOError: If file cannot be written
    """
    eligible_count = sum(
        1 for s in scholarships
        if s.get("match_result", {}).get("eligible", False)
    )
    
    export_data = {
        "exported_at": datetime.now().isoformat(),
        "profile_hash": _get_profile_hash(scholarships),
        "total_scholarships": len(scholarships),
        "eligible_count": eligible_count,
        "scholarships": [
            {
                "rank": i + 1,
                "title": s.get("title", "Unknown"),
                "source": s.get("source", "Unknown"),
                "amount_min": s.get("amount_min"),
                "amount_max": s.get("amount_max"),
                "deadline": s.get("deadline"),
                "fit_score": s.get("fit_score", 0),
                "fit_score_breakdown": s.get("fit_score_breakdown", {}),
                "eligible": s.get("match_result", {}).get("eligible", False),
                "match_result": s.get("match_result", {}),
                "application_url": s.get("application_url"),
            }
            for i, s in enumerate(
                sorted(
                    scholarships,
                    key=lambda x: x.get("fit_score", 0),
                    reverse=True,
                )
            )
        ],
    }
    
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)


def export_csv(
    scholarships: List[Dict[str, Any]],
    filepath: str,
) -> None:
    """Export scholarships to CSV format.
    
    Args:
        scholarships: List of scholarship dictionaries with match results
        filepath: Path to write CSV file
        
    Raises:
        IOError: If file cannot be written
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Sort by fit score
    sorted_scholarships = sorted(
        scholarships,
        key=lambda x: x.get("fit_score", 0),
        reverse=True,
    )
    
    fieldnames = [
        "rank",
        "title",
        "source",
        "amount",
        "deadline",
        "fit_score",
        "eligible",
        "application_url",
    ]
    
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for i, scholarship in enumerate(sorted_scholarships, 1):
            # Format amount as range or single value
            amount_min = scholarship.get("amount_min")
            amount_max = scholarship.get("amount_max")
            
            if amount_max and amount_min and amount_max != amount_min:
                amount = f"${amount_min // 100:,} - ${amount_max // 100:,}"
            elif amount_max:
                amount = f"${amount_max // 100:,}"
            elif amount_min:
                amount = f"${amount_min // 100:,}+"
            else:
                amount = "Varies"
            
            fit_score = scholarship.get("fit_score", 0)
            fit_pct = int(fit_score * 100)
            
            writer.writerow({
                "rank": i,
                "title": scholarship.get("title", "Unknown"),
                "source": scholarship.get("source", "Unknown"),
                "amount": amount,
                "deadline": scholarship.get("deadline", "Open/Rolling"),
                "fit_score": f"{fit_pct}%",
                "eligible": "Yes" if scholarship.get("match_result", {}).get("eligible", False) else "No",
                "application_url": scholarship.get("application_url", ""),
            })


def export_markdown(
    scholarships: List[Dict[str, Any]],
    filepath: str,
) -> None:
    """Export scholarships to Markdown format.
    
    Args:
        scholarships: List of scholarship dictionaries with match results
        filepath: Path to write Markdown file
        
    Raises:
        IOError: If file cannot be written
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Sort by fit score
    sorted_scholarships = sorted(
        scholarships,
        key=lambda x: x.get("fit_score", 0),
        reverse=True,
    )
    
    lines = []
    
    # Header
    lines.append("# Scholarship Matches")
    lines.append("")
    lines.append(f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Total Scholarships:** {len(scholarships)}")
    eligible_count = sum(
        1 for s in scholarships
        if s.get("match_result", {}).get("eligible", False)
    )
    lines.append(f"**Eligible:** {eligible_count}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Scholarships
    for i, scholarship in enumerate(sorted_scholarships, 1):
        title = scholarship.get("title", "Unknown")
        lines.append(f"## {i}. {title}")
        lines.append("")
        
        # Source and fit score
        source = scholarship.get("source", "Unknown")
        fit_score = scholarship.get("fit_score", 0)
        fit_pct = int(fit_score * 100)
        eligible = scholarship.get("match_result", {}).get("eligible", False)
        
        lines.append(f"**Source:** {source}")
        lines.append(f"**Fit Score:** {fit_pct}%")
        lines.append(f"**Eligible:** {'✓ Yes' if eligible else '✗ No'}")
        lines.append("")
        
        # Amount
        amount_min = scholarship.get("amount_min")
        amount_max = scholarship.get("amount_max")
        
        if amount_max and amount_min and amount_max != amount_min:
            amount = f"${amount_min // 100:,} - ${amount_max // 100:,}"
        elif amount_max:
            amount = f"${amount_max // 100:,}"
        elif amount_min:
            amount = f"${amount_min // 100:,}+"
        else:
            amount = "Varies"
        
        lines.append(f"**Amount:** {amount}")
        
        # Deadline
        deadline = scholarship.get("deadline")
        if deadline:
            lines.append(f"**Deadline:** {deadline}")
        else:
            lines.append("**Deadline:** Open/Rolling")
        
        lines.append("")
        
        # Application URL
        url = scholarship.get("application_url")
        if url:
            lines.append(f"**Apply:** [{url}]({url})")
            lines.append("")
        
        # Match details
        match_result = scholarship.get("match_result", {})
        if match_result:
            lines.append("### Requirements")
            lines.append("")
            
            details = match_result.get("details", [])
            if details:
                for detail in details:
                    req = detail.get("requirement", "Unknown")
                    status = detail.get("status", "unknown")
                    user_val = detail.get("user_value", "")
                    
                    if status == "matched":
                        icon = "✓"
                    elif status == "partial":
                        icon = "~"
                    elif status == "unmatched":
                        icon = "✗"
                    else:
                        icon = "?"
                    
                    lines.append(f"- {icon} {req}")
                    if user_val and user_val != "Not specified":
                        lines.append(f"  - Your value: {user_val}")
            
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def export_scholarships(
    scholarships: List[Dict[str, Any]],
    filepath: str,
) -> None:
    """Export scholarships with format auto-detection from file extension.
    
    Args:
        scholarships: List of scholarship dictionaries with match results
        filepath: Path to write file (extension determines format)
        
    Raises:
        ValueError: If file extension is not recognized
        IOError: If file cannot be written
    """
    path = Path(filepath)
    extension = path.suffix.lower()
    
    if extension == ".json":
        export_json(scholarships, filepath)
    elif extension == ".csv":
        export_csv(scholarships, filepath)
    elif extension in (".md", ".markdown"):
        export_markdown(scholarships, filepath)
    else:
        raise ValueError(
            f"Unsupported file format: {extension}. "
            "Supported formats: .json, .csv, .md, .markdown"
        )
