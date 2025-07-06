#!/usr/bin/env python3
"""
Shared utilities for the buying group monitor
"""

import time
import requests
from typing import Optional
from config import REQUEST_TIMEOUT, MAX_RETRIES, RETRY_DELAY
import logging

def make_request_with_retry(method: str, url: str, logger: logging.Logger, **kwargs) -> Optional[requests.Response]:
    """Make HTTP request with retry logic and proper error handling."""
    for attempt in range(MAX_RETRIES + 1):
        try:
            kwargs.setdefault('timeout', REQUEST_TIMEOUT)
            response = getattr(requests.Session(), method.lower())(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * (2 ** attempt))  # Exponential backoff
            else:
                logger.error(f"All {MAX_RETRIES + 1} request attempts failed")
                return None
    return None 