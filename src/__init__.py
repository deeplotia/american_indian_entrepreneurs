"""Project package for American Indian Entrepreneurs.

Exposes core modules under the `src` package namespace.
"""

__all__ = [
    "models",
    "http",
    "scrapers",
    "fetchers",
    "run",
]

# Re-export commonly used classes for convenience
from src.models.company_details import CompanyDetails  # noqa: F401
from src.fetchers.company_details_fetcher import CompanyDetailsFetcher  # noqa: F401


