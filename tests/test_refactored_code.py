#!/usr/bin/env python3
"""
Pytest-based tests for the refactored American Indian Entrepreneurs codebase.
"""

import logging

def test_imports():
    """Test that all core modules/classes can be imported successfully."""
    from src.fetch_company_details import (
        CompanyDetails,
        HTTPClient,
        BaseScraper,
        GoogleFinanceScraper,
        CNBCScraper,
        CNNScraper,
        MarketWatchScraper,
        YahooFinanceScraper,
        CompanyDetailsFetcher,
    )

    # Basic sanity asserts
    assert CompanyDetails is not None
    assert HTTPClient is not None
    assert BaseScraper is not None

def test_company_details():
    """Test the CompanyDetails dataclass."""
    from src.fetch_company_details import CompanyDetails

    details = CompanyDetails()
    assert details.ceo is None
    assert details.employees is None
    assert details.headquarters is None
    assert details.founded is None
    assert details.industry is None
    assert len(details.sources) == 0
    assert len(details.urls) == 0

    # is_complete should be False for empty instance
    assert not details.is_complete()

    # to_dict should provide empty-string values for missing fields
    details_dict = details.to_dict()
    assert isinstance(details_dict, dict)
    assert details_dict["ceo"] == ""
    assert details_dict["employees"] == ""

def test_http_client():
    """Test the HTTPClient class basic behavior."""
    from src.fetch_company_details import HTTPClient

    client = HTTPClient()
    assert hasattr(client, "headers")
    assert "User-Agent" in client.headers
    assert "X-Forwarded-For" in client.headers

def test_scrapers():
    """Test scraper class instantiation and base interface."""
    from src.fetch_company_details import (
        HTTPClient,
        GoogleFinanceScraper,
        CNBCScraper,
        CNNScraper,
        MarketWatchScraper,
        YahooFinanceScraper,
        BaseScraper,
    )

    http_client = HTTPClient()
    scrapers = [
        GoogleFinanceScraper(http_client),
        CNBCScraper(http_client),
        CNNScraper(http_client),
        MarketWatchScraper(http_client),
        YahooFinanceScraper(http_client),
    ]

    for scraper in scrapers:
        assert isinstance(scraper, BaseScraper)
        assert hasattr(scraper, "scrape")
        assert hasattr(scraper, "_add_source")

def test_company_details_fetcher():
    """Test the CompanyDetailsFetcher class interfaces and helpers."""
    from src.fetch_company_details import CompanyDetailsFetcher

    fetcher = CompanyDetailsFetcher(max_workers=2)
    assert hasattr(fetcher, "fetch_company_details")
    assert hasattr(fetcher, "fetch_multiple_companies")
    assert hasattr(fetcher, "_clean_ticker")

    # Test ticker cleaning
    assert fetcher._clean_ticker("AAPL^") == "AAPL"
    assert fetcher._clean_ticker("MSFT/") == "MSFT"
    assert fetcher._clean_ticker(" GOOGL ") == "GOOGL"

def test_data_processor():
    """Test the DataProcessor and DataExporter classes are importable and basic attributes exist."""
    from src.run import DataProcessor, DataExporter

    processor = DataProcessor(max_workers=2, batch_size=10)
    assert hasattr(processor, "process_stock_data")
    assert hasattr(processor, "_add_company_detail_columns")
    assert hasattr(processor, "_process_companies_batch")

    exporter = DataExporter()
    assert hasattr(exporter, "export_to_csv")
    assert hasattr(exporter, "export_to_excel")

def setup_module():
    """Configure logging for test runs."""
    logging.basicConfig(level=logging.WARNING)
