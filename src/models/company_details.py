from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set


@dataclass
class CompanyDetails:
    """Data class to store company information."""

    ceo: Optional[str] = None
    employees: Optional[str] = None
    headquarters: Optional[str] = None
    founded: Optional[str] = None
    industry: Optional[str] = None
    sources: Set[str] = field(default_factory=set)
    urls: Set[str] = field(default_factory=set)

    def is_complete(self) -> bool:
        """Check if all required fields are populated."""
        return all(
            [
                self.ceo is not None,
                self.employees is not None,
                self.headquarters is not None,
                self.founded is not None,
                self.industry is not None,
            ]
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DataFrame storage."""
        return {
            "ceo": self.ceo or "",
            "employees": self.employees or "",
            "headquarters": self.headquarters or "",
            "founded": self.founded or "",
            "industry": self.industry or "",
            "sources": ",".join(self.sources) if self.sources else "",
            "urls": ",".join(self.urls) if self.urls else "",
        }


