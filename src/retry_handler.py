#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Retry Handler - Error recovery utilities for AI Employee watchers.

Provides retry logic with exponential backoff for handling transient errors
like network timeouts, API rate limits, and temporary connection failures.

Usage:
    @with_retry(max_attempts=3, base_delay=1, max_delay=60)
    def fetch_data():
        # Code that might fail transiently
        pass
"""

import time
import logging
from functools import wraps
from typing import Callable, Any, Optional


logger = logging.getLogger(__name__)


class TransientError(Exception):
    """
    Exception indicating a transient/recoverable error.
    
    Use this for errors that might succeed on retry:
    - Network timeouts
    - API rate limits
    - Temporary connection failures
    - Resource temporarily unavailable
    """
    pass


class PermanentError(Exception):
    """
    Exception indicating a permanent/non-recoverable error.
    
    Use this for errors that should NOT be retried:
    - Authentication failures
    - Invalid credentials
    - Permission denied
    - Invalid input data
    """
    pass


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: int = 2,
    jitter: bool = True
) -> Callable:
    """
    Decorator for adding retry logic with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay cap in seconds (default: 60.0)
        exponential_base: Base for exponential backoff (default: 2)
        jitter: Add random jitter to prevent thundering herd (default: True)
    
    Returns:
        Decorated function with retry logic
    
    Example:
        @with_retry(max_attempts=3, base_delay=1)
        def fetch_email():
            response = requests.get(email_api_url)
            if response.status_code == 429:  # Rate limited
                raise TransientError("Rate limited")
            return response.json()
    """
    import random
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                    
                except TransientError as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(f"Max attempts ({max_attempts}) reached for {func.__name__}")
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    # Add jitter to prevent synchronized retries
                    if jitter:
                        jitter_value = random.uniform(0, delay * 0.1)
                        delay += jitter_value
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    
                    time.sleep(delay)
                    
                except PermanentError as e:
                    # Don't retry permanent errors
                    logger.error(f"Permanent error in {func.__name__}: {e}")
                    raise
                    
                except Exception as e:
                    # Treat unexpected errors as transient
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(
                            f"Unexpected error after {max_attempts} attempts in {func.__name__}: {e}"
                        )
                        raise
                    
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    if jitter:
                        jitter_value = random.uniform(0, delay * 0.1)
                        delay += jitter_value
                    
                    logger.warning(
                        f"Unexpected error on attempt {attempt + 1}/{max_attempts} for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    
                    time.sleep(delay)
            
            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


def retry_with_timeout(
    timeout: float,
    max_attempts: int = 3,
    base_delay: float = 1.0
) -> Callable:
    """
    Decorator combining retry logic with overall timeout.
    
    Args:
        timeout: Total timeout in seconds for all attempts combined
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay between attempts
    
    Returns:
        Decorated function with retry and timeout
    
    Example:
        @retry_with_timeout(timeout=30, max_attempts=3)
        def fetch_with_deadline():
            # Will retry but give up after 30 seconds total
            pass
    """
    import random
    from functools import wraps
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                    
                except (TransientError, Exception) as e:
                    last_exception = e
                    
                    # Check if we've exceeded total timeout
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        logger.error(f"Timeout ({timeout}s) exceeded for {func.__name__}")
                        raise TimeoutError(f"Operation timed out after {timeout}s") from e
                    
                    if attempt == max_attempts - 1:
                        logger.error(f"Max attempts ({max_attempts}) reached for {func.__name__}")
                        raise
                    
                    # Calculate remaining time for delay
                    remaining = timeout - (time.time() - start_time)
                    delay = min(base_delay * (2 ** attempt), remaining * 0.5)
                    delay += random.uniform(0, delay * 0.1)  # Jitter
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    
                    time.sleep(delay)
            
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


class RetryContext:
    """
    Context manager for explicit retry control.
    
    Use when decorator pattern doesn't fit your use case.
    
    Example:
        with RetryContext(max_attempts=3) as retry:
            for attempt in retry:
                try:
                    result = do_something()
                    break
                except TransientError as e:
                    if not retry.can_retry():
                        raise
                    retry.wait()
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.attempt = 0
        self.last_exception = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False  # Don't suppress exceptions
    
    def __iter__(self):
        for self.attempt in range(self.max_attempts):
            yield self.attempt
    
    def can_retry(self) -> bool:
        """Check if more retry attempts are available."""
        return self.attempt < self.max_attempts - 1
    
    def wait(self):
        """Wait before next retry with exponential backoff."""
        if not self.can_retry():
            return
        
        delay = min(self.base_delay * (2 ** self.attempt), self.max_delay)
        import random
        delay += random.uniform(0, delay * 0.1)  # Jitter
        
        logger.info(f"Waiting {delay:.2f}s before retry {self.attempt + 2}/{self.max_attempts}")
        time.sleep(delay)


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.DEBUG)
    
    @with_retry(max_attempts=3, base_delay=0.5)
    def flaky_function():
        import random
        if random.random() < 0.7:  # 70% chance of failure
            raise TransientError("Random failure")
        return "Success!"
    
    print("Testing retry logic...")
    try:
        result = flaky_function()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Failed after retries: {e}")
