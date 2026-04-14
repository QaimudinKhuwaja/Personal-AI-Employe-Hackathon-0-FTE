"""
Retry Handler

Implements exponential backoff and retry logic for transient failures.
Used by all external API integrations (Odoo, Facebook, Gmail, etc.).

Usage:
    from retry_handler import with_retry, CircuitBreaker
    
    @with_retry(max_attempts=3, base_delay=1)
    def api_call():
        # API call that might fail
        pass
    
    # Or use circuit breaker for critical services
    breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
    if breaker.can_execute():
        api_call()
"""

import time
import logging
import functools
from typing import Any, Callable, Optional, Type
from datetime import datetime, timedelta
from pathlib import Path
import json


class RetryError(Exception):
    """Exception raised when all retry attempts fail."""
    pass


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit Breaker pattern implementation.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failure threshold exceeded, requests blocked
    - HALF_OPEN: Recovery timeout elapsed, test request allowed
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 1
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying again
            half_open_max_calls: Max calls in half-open state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.half_open_calls = 0
        
        self.logger = logging.getLogger(f'CircuitBreaker.{id(self)}')
    
    def can_execute(self) -> bool:
        """
        Check if execution is allowed.
        
        Returns:
            True if request can proceed
        """
        if self.state == 'CLOSED':
            return True
        
        if self.state == 'OPEN':
            # Check if recovery timeout has elapsed
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self.logger.info('Circuit breaker moving to HALF_OPEN state')
                    self.state = 'HALF_OPEN'
                    self.half_open_calls = 0
                    return True
            return False
        
        if self.state == 'HALF_OPEN':
            # Allow limited calls in half-open state
            if self.half_open_calls < self.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False
        
        return False
    
    def record_success(self):
        """Record a successful execution."""
        if self.state == 'HALF_OPEN':
            self.logger.info('Circuit breaker moving to CLOSED state (success in HALF_OPEN)')
            self.state = 'CLOSED'
            self.failure_count = 0
            self.half_open_calls = 0
        elif self.state == 'CLOSED':
            # Reset failure count on success
            self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self):
        """Record a failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == 'HALF_OPEN':
            self.logger.warning('Circuit breaker moving to OPEN state (failure in HALF_OPEN)')
            self.state = 'OPEN'
        elif self.state == 'CLOSED' and self.failure_count >= self.failure_threshold:
            self.logger.warning(f'Circuit breaker moving to OPEN state ({self.failure_count} failures)')
            self.state = 'OPEN'
    
    def get_state(self) -> dict:
        """Get current circuit breaker state."""
        return {
            'state': self.state,
            'failure_count': self.failure_count,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'half_open_calls': self.half_open_calls
        }


# Global circuit breakers for different services
_circuit_breakers = {}

def get_circuit_breaker(service_name: str) -> Optional[CircuitBreaker]:
    """Get or create circuit breaker for a service."""
    if service_name not in _circuit_breakers:
        _circuit_breakers[service_name] = CircuitBreaker()
    return _circuit_breakers[service_name]


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
    circuit_breaker_name: str = None
):
    """
    Decorator for retry logic with exponential backoff.
    
    Args:
        max_attempts: Maximum retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        exceptions: Tuple of exceptions to catch
        circuit_breaker_name: Name of circuit breaker to use
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    # Check circuit breaker if configured
                    if circuit_breaker_name:
                        breaker = get_circuit_breaker(circuit_breaker_name)
                        if not breaker.can_execute():
                            raise CircuitBreakerOpen(
                                f'Circuit breaker {circuit_breaker_name} is OPEN'
                            )
                    
                    # Execute function
                    result = func(*args, **kwargs)
                    
                    # Record success
                    if circuit_breaker_name:
                        breaker.record_success()
                    
                    return result
                    
                except exceptions as e:
                    last_exception = e
                    
                    # Record failure
                    if circuit_breaker_name:
                        breaker = get_circuit_breaker(circuit_breaker_name)
                        breaker.record_failure()
                    
                    # Don't retry on last attempt
                    if attempt == max_attempts:
                        break
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
                    
                    # Add jitter (±10%)
                    import random
                    jitter = delay * 0.1 * (2 * random.random() - 1)
                    delay = delay + jitter
                    
                    logging.warning(
                        f'{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. '
                        f'Retrying in {delay:.2f}s...'
                    )
                    
                    time.sleep(delay)
            
            # All attempts failed
            raise RetryError(
                f'{func.__name__} failed after {max_attempts} attempts. '
                f'Last error: {last_exception}'
            ) from last_exception
        
        return wrapper
    return decorator


class RetryHandler:
    """
    Class-based retry handler for more complex scenarios.
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        logger: logging.Logger = None
    ):
        """
        Initialize retry handler.
        
        Args:
            max_attempts: Maximum retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            logger: Logger instance
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.logger = logger or logging.getLogger('RetryHandler')
    
    def execute(
        self,
        func: Callable,
        *args,
        exceptions: tuple = (Exception,),
        on_retry: Callable = None,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            args: Positional arguments
            exceptions: Tuple of exceptions to catch
            on_retry: Callback function called on each retry
            kwargs: Keyword arguments
            
        Returns:
            Function result
        """
        last_exception = None
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                return func(*args, **kwargs)
                
            except exceptions as e:
                last_exception = e
                
                if attempt == self.max_attempts:
                    break
                
                # Calculate delay
                delay = min(
                    self.base_delay * (2 ** (attempt - 1)),
                    self.max_delay
                )
                
                self.logger.warning(
                    f'Attempt {attempt}/{self.max_attempts} failed: {e}. '
                    f'Retrying in {delay:.2f}s...'
                )
                
                # Call retry callback if provided
                if on_retry:
                    on_retry(attempt, e, delay)
                
                time.sleep(delay)
        
        raise RetryError(
            f'Failed after {self.max_attempts} attempts. '
            f'Last error: {last_exception}'
        ) from last_exception


# Quarantine manager for problematic items
class QuarantineManager:
    """
    Manages quarantine for items that consistently fail processing.
    """
    
    def __init__(self, quarantine_dir: str = 'AI_Employee_Vault/Quarantine'):
        """
        Initialize quarantine manager.
        
        Args:
            quarantine_dir: Directory for quarantined items
        """
        self.quarantine_dir = Path(quarantine_dir)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger('QuarantineManager')
    
    def quarantine(
        self,
        item_id: str,
        item_type: str,
        error: str,
        attempts: int,
        original_path: Path = None
    ) -> Path:
        """
        Move item to quarantine.
        
        Args:
            item_id: Unique item identifier
            item_type: Type of item
            error: Error message
            attempts: Number of failed attempts
            original_path: Original file path
            
        Returns:
            Path to quarantined item
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        quarantine_file = self.quarantine_dir / f'{item_type}_{item_id}_{timestamp}.md'
        
        # Create quarantine record
        content = f"""---
quarantined: {datetime.now().isoformat()}
item_id: {item_id}
item_type: {item_type}
error: {error}
attempts: {attempts}
original_path: {original_path}
status: pending_review
---

# Quarantined Item

This item has been quarantined due to repeated processing failures.

## Error Details
{error}

## Failed Attempts
{attempts}

## Review Actions
- [ ] Review error and fix if needed
- [ ] Move back to Needs_Action for reprocessing
- [ ] Delete if item is invalid
"""
        
        quarantine_file.write_text(content, encoding='utf-8')
        
        self.logger.warning(f'Quarantined {item_type} item: {item_id}')
        
        return quarantine_file
    
    def list_quarantined(self) -> list:
        """List all quarantined items."""
        items = []
        for file in self.quarantine_dir.glob('*.md'):
            try:
                content = file.read_text(encoding='utf-8')
                # Parse frontmatter (simplified)
                items.append({
                    'file': str(file),
                    'name': file.name,
                    'quarantined_at': file.stat().st_mtime
                })
            except Exception as e:
                self.logger.warning(f'Could not read {file.name}: {e}')
        
        return items
    
    def release(self, item_file: str, destination: str) -> bool:
        """
        Release item from quarantine.
        
        Args:
            item_file: Path to quarantined item
            destination: Destination folder
            
        Returns:
            True if successful
        """
        try:
            src = Path(item_file)
            dst = Path(destination) / src.name
            
            dst.mkdir(parents=True, exist_ok=True)
            src.rename(dst)
            
            self.logger.info(f'Released quarantined item: {src.name}')
            return True
            
        except Exception as e:
            self.logger.error(f'Failed to release item: {e}')
            return False


if __name__ == '__main__':
    # Test retry handler
    logging.basicConfig(level=logging.INFO)
    
    # Test decorator
    @with_retry(max_attempts=3, base_delay=0.5)
    def flaky_function():
        import random
        if random.random() < 0.7:  # 70% failure rate
            raise Exception('Simulated failure')
        return 'Success!'
    
    try:
        result = flaky_function()
        print(f'Result: {result}')
    except RetryError as e:
        print(f'Failed: {e}')
    
    # Test circuit breaker
    print('\nTesting circuit breaker...')
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=5)
    
    for i in range(5):
        if breaker.can_execute():
            print(f'Call {i+1}: Allowed')
            breaker.record_failure()
        else:
            print(f'Call {i+1}: Blocked (circuit OPEN)')
        
        print(f'State: {breaker.get_state()}')
        time.sleep(1)
