import logging
import random
import time
from typing import Optional

import requests
from faker import Faker


logger = logging.getLogger(__name__)


# HTTP configuration constants
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

REQUEST_TIMEOUT = 30
MAX_RETRIES = 2
RETRY_DELAY = 1.0
RATE_LIMIT_DELAY = 1.0


class HTTPClient:
    """Handles HTTP requests with proper error handling and retry logic."""

    def __init__(self):
        self.fake = Faker()
        self.session = requests.Session()
        self.last_request_time = 0
        self._update_headers()

    def _update_headers(self):
        """Update request headers with random user agent and more realistic headers."""
        self.fake.seed_instance(random.randint(0, 1000))
        ip = self.fake.ipv4()

        self.headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "X-Forwarded-For": ip,
            "X-Real-Ip": ip,
            "X-Requested-With": "XMLHttpRequest",
        }

    def _rate_limit_delay(self):
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - time_since_last_request)
        self.last_request_time = time.time()

    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Make HTTP GET request with improved retry logic and rate limiting."""
        self._rate_limit_delay()

        for attempt in range(MAX_RETRIES):
            try:
                self._update_headers()

                if "google.com" in url:
                    kwargs["cookies"] = {"CONSENT": "YES+", "NID": "511=abc123"}
                elif "yahoo.com" in url:
                    kwargs["cookies"] = {
                        "A1": "d=AQABBJ...; Expires=Tue, 19 Jan 2038 03:14:07 GMT; Path=/; Domain=.yahoo.com; Secure; HttpOnly",
                        "A3": "d=AQABBJ...; Expires=Tue, 19 Jan 2038 03:14:07 GMT; Path=/; Domain=.yahoo.com; Secure; HttpOnly",
                    }
                elif "marketwatch.com" in url:
                    kwargs["cookies"] = {"wsod_region": "us", "wsod_language": "en"}

                response = self.session.get(
                    url, headers=self.headers, timeout=REQUEST_TIMEOUT, **kwargs
                )

                status = response.status_code
                if status < 300:
                    return response

                if status == 429:
                    logger.warning(
                        f"Rate limited (429) for {url}, attempt {attempt + 1}/{MAX_RETRIES}"
                    )
                    if attempt < MAX_RETRIES - 1:
                        backoff = (2 ** attempt) * RATE_LIMIT_DELAY * 2
                        time.sleep(backoff)
                        continue
                    return None

                if status == 403:
                    logger.warning(
                        f"Forbidden (403) for {url}, attempt {attempt + 1}/{MAX_RETRIES}"
                    )
                    if attempt < MAX_RETRIES - 1:
                        self._update_headers()
                        time.sleep(RETRY_DELAY)
                        continue
                    return None

                if status in (400, 401, 404, 405, 410):
                    logger.info(f"HTTP {status} for {url}; skipping retries")
                    return None

                if status >= 500:
                    logger.warning(
                        f"Server error {status} for {url}, attempt {attempt + 1}/{MAX_RETRIES}"
                    )
                    if attempt < MAX_RETRIES - 1:
                        time.sleep((2 ** attempt) * RETRY_DELAY)
                        continue
                    return None

            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
            ) as error:
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {error}"
                )
                if attempt < MAX_RETRIES - 1:
                    time.sleep((2 ** attempt) * RETRY_DELAY)
                else:
                    return None

        return None


