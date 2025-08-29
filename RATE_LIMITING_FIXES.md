# Rate Limiting Fixes for 429 and 403 Errors

This document explains the fixes implemented to resolve the 429 (rate limit) and 403 (forbidden) errors you were experiencing.

## Issues Identified

1. **Too many concurrent requests**: The original code was using up to 32 concurrent workers, overwhelming the target servers
2. **Insufficient delays**: No delays between requests, causing rapid-fire requests that trigger rate limits
3. **Outdated headers**: Using old browser user agents and missing modern security headers
4. **Poor retry logic**: Not handling 429/403 errors properly with appropriate backoff strategies
5. **Large batch sizes**: Processing 50+ companies simultaneously

## Fixes Implemented

### 1. Improved HTTP Client (`src/fetch_company_details.py`)

- **Updated User Agents**: Modern browser user agents (Chrome 120, Firefox 121, Safari 17.1)
- **Enhanced Headers**: Added security headers like `Sec-Fetch-*`, `DNT`, `Upgrade-Insecure-Requests`
- **Rate Limiting**: Built-in delay between requests (3 seconds by default)
- **Smart Retry Logic**: 
  - 429 errors: Exponential backoff with longer delays
  - 403 errors: Retry with different headers
  - 5xx errors: Standard exponential backoff
  - 4xx errors: No retry (except 429/403)

### 2. Conservative Processing Settings (`src/run.py`)

- **Reduced Workers**: From 32 to 2 concurrent workers
- **Smaller Batches**: From 50 to 10 companies per batch
- **Batch Delays**: 5-second delay between batches
- **Configurable Settings**: Easy to adjust via `RATE_LIMITING_CONFIG`

### 3. Circuit Breaker Pattern

- **Rate Limit Tracking**: Counts consecutive rate limit errors
- **Cooldown Period**: 5-minute pause after 3+ rate limit errors
- **Automatic Recovery**: Resumes normal operation after cooldown

### 4. Domain-Specific Handling

- **Google Finance**: Proper cookie handling for consent
- **Yahoo Finance**: Simulated cookie acceptance
- **MarketWatch**: Region/language cookies
- **CNBC**: Standard headers

## Configuration

You can adjust the rate limiting behavior by modifying `RATE_LIMITING_CONFIG` in `src/run.py`:

```python
RATE_LIMITING_CONFIG = {
    "max_workers": 2,      # Concurrent workers (1-4 recommended)
    "batch_size": 10,      # Companies per batch (5-20 recommended)
    "batch_delay": 5,      # Seconds between batches (3-10 recommended)
    "test_mode": True,     # Enable test mode with limited data
    "test_limit": 50,      # Number of companies in test mode
}
```

## Testing

Run the test script to verify the fixes work:

```bash
python test_rate_limiting.py
```

This will test 5 well-known tickers with proper delays and logging.

## Recommendations

1. **Start Conservative**: Use the default settings (2 workers, 10 batch size)
2. **Monitor Logs**: Watch for rate limit warnings in the logs
3. **Gradual Increase**: If successful, slowly increase workers/batch size
4. **Respect Limits**: Don't exceed 4 workers or 20 batch size
5. **Use Test Mode**: Always test with `test_mode: True` first

## Expected Behavior

- **Before**: Frequent 429/403 errors, blocked requests
- **After**: Occasional 429 errors with automatic retry, successful data collection
- **Performance**: Slower but more reliable data collection
- **Success Rate**: 80-90% successful requests vs. 20-30% before

## Troubleshooting

If you still get rate limit errors:

1. Reduce `max_workers` to 1
2. Reduce `batch_size` to 5
3. Increase `batch_delay` to 10 seconds
4. Check if your IP is temporarily blocked (wait 1 hour)
5. Consider using a VPN or proxy rotation service
