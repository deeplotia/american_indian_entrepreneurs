#!/usr/bin/env python3
"""
Test script to verify rate limiting fixes work properly.
"""

import time
import logging
from src.fetch_company_details import CompanyDetailsFetcher

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_rate_limiting():
    """Test the rate limiting improvements."""
    logger.info("Testing rate limiting improvements...")
    
    # Initialize fetcher with conservative settings
    fetcher = CompanyDetailsFetcher(max_workers=1)
    
    # Test with a few well-known tickers
    test_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    
    for i, ticker in enumerate(test_tickers):
        logger.info(f"Testing ticker {i+1}/{len(test_tickers)}: {ticker}")
        
        try:
            details = fetcher.fetch_company_details(ticker)
            
            # Log what we found
            found_fields = []
            if details.ceo:
                found_fields.append("CEO")
            if details.employees:
                found_fields.append("Employees")
            if details.headquarters:
                found_fields.append("Headquarters")
            if details.founded:
                found_fields.append("Founded")
            if details.industry:
                found_fields.append("Industry")
            
            logger.info(f"Found data for {ticker}: {', '.join(found_fields) if found_fields else 'None'}")
            
            # Add delay between requests
            if i < len(test_tickers) - 1:
                logger.info("Waiting 5 seconds before next request...")
                time.sleep(5)
                
        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}")
    
    logger.info("Rate limiting test completed!")

if __name__ == "__main__":
    test_rate_limiting()
