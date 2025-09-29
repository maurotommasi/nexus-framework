import time
import functools
from datetime import datetime, timedelta, timezone
from typing import Callable, Any, Optional, Dict
import random

class TimeUtils:
    """Time-related utilities."""
    
    @staticmethod
    def get_timestamp(utc: bool = True) -> str:
        """Get current timestamp."""
        result = datetime.utcnow().isoformat() + 'Z' if utc else datetime.now().isoformat()
        return result
        # Examples:
        # TimeUtils.get_timestamp()
        # -> "2025-09-22T12:34:56.789Z"
        #
        # TimeUtils.get_timestamp(utc=False)
        # -> "2025-09-22T14:34:56.789"

    @staticmethod
    def get_unix_timestamp() -> int:
        """Get current Unix timestamp."""
        return int(time.time())
        # Examples:
        # TimeUtils.get_unix_timestamp()
        # -> 1758513296

    @staticmethod
    def parse_iso_timestamp(timestamp: str) -> datetime:
        """Parse ISO timestamp string to datetime object."""
        if timestamp.endswith('Z'):
            timestamp = timestamp[:-1] + '+00:00'
        return datetime.fromisoformat(timestamp)
        # Examples:
        # TimeUtils.parse_iso_timestamp("2025-09-22T12:34:56Z")
        # -> datetime(2025, 9, 22, 12, 34, 56, tzinfo=datetime.timezone.utc)

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in seconds to human-readable string."""
        if seconds < 60:
            return f"{seconds:.2f}s"
        elif seconds < 3600:
            minutes, secs = divmod(seconds, 60)
            return f"{int(minutes)}m {secs:.1f}s"
        else:
            hours, remainder = divmod(seconds, 3600)
            minutes, secs = divmod(remainder, 60)
            return f"{int(hours)}h {int(minutes)}m {secs:.0f}s"
        # Examples:
        # TimeUtils.format_duration(45.5)
        # -> "45.50s"
        #
        # TimeUtils.format_duration(125)
        # -> "2m 5.0s"
        #
        # TimeUtils.format_duration(3661)
        # -> "1h 1m 1s"

    @staticmethod
    def add_time(base_time: datetime, **kwargs) -> datetime:
        """Add time delta to base time."""
        delta = timedelta(**kwargs)
        return base_time + delta
        # Examples:
        # now = datetime(2025, 9, 22, 12, 0, 0)
        # TimeUtils.add_time(now, hours=1, minutes=30)
        # -> datetime(2025, 9, 22, 13, 30, 0)

    @staticmethod
    def time_until(target_time: datetime, from_time: datetime = None) -> timedelta:
        """Calculate time until target time."""
        if from_time is None:
            from_time = datetime.utcnow()
        return target_time - from_time
        # Examples:
        # now = datetime(2025, 9, 22, 12, 0, 0)
        # target = datetime(2025, 9, 22, 15, 0, 0)
        # TimeUtils.time_until(target, now)
        # -> timedelta(seconds=10800)

    @staticmethod
    def is_business_hours(dt: datetime = None, start_hour: int = 9, 
                         end_hour: int = 17, weekdays_only: bool = True) -> bool:
        """Check if datetime is within business hours."""
        if dt is None:
            dt = datetime.now()
        if weekdays_only and dt.weekday() >= 5:
            return False
        return start_hour <= dt.hour < end_hour
        # Examples:
        # monday = datetime(2025, 9, 22, 10, 0, 0)
        # TimeUtils.is_business_hours(monday)
        # -> True
        #
        # saturday = datetime(2025, 9, 27, 10, 0, 0)
        # TimeUtils.is_business_hours(saturday)
        # -> False

    @staticmethod
    def get_time_zones() -> Dict[str, str]:
        """Get common time zones."""
        return {
            'UTC': '+00:00',
            'EST': '-05:00',
            'PST': '-08:00',
            'GMT': '+00:00',
            'CET': '+01:00',
            'JST': '+09:00'
        }
        # Examples:
        # TimeUtils.get_time_zones()
        # -> { 'UTC': '+00:00', 'EST': '-05:00', ... }

class RetryUtils:
    """Retry mechanism utilities."""
    
    @staticmethod
    def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0,
              exceptions: tuple = (Exception,), jitter: bool = True):
        """Decorator for retrying function calls with exponential backoff."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt == max_attempts - 1:
                            raise last_exception
                        current_delay = delay * (backoff ** attempt)
                        if jitter:
                            current_delay *= (0.5 + random.random() * 0.5)
                        print(f"Attempt {attempt + 1} failed: {e}. Retrying in {current_delay:.2f}s...")
                        time.sleep(current_delay)
                raise last_exception
            return wrapper
        return decorator
        # Examples:
        # @RetryUtils.retry(max_attempts=3, delay=1)
        # def flaky():
        #     raise ValueError("Fail!")
        # flaky()

    @staticmethod
    def retry_with_condition(condition_func: Callable[[Any], bool], max_attempts: int = 3,
                           delay: float = 1.0, backoff: float = 2.0):
        """Retry based on condition function result."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                for attempt in range(max_attempts):
                    result = func(*args, **kwargs)
                    if condition_func(result):
                        return result
                    if attempt == max_attempts - 1:
                        return result
                    current_delay = delay * (backoff ** attempt)
                    time.sleep(current_delay)
                return result
            return wrapper
        return decorator
        # Examples:
        # @RetryUtils.retry_with_condition(lambda x: x == "ok", max_attempts=3)
        # def sometimes():
        #     return random.choice(["fail", "ok"])
        # sometimes()

    @staticmethod
    def wait_for_condition(condition_func: Callable[[], bool], timeout: float = 30.0,
                          interval: float = 1.0, description: str = "condition") -> bool:
        """Wait for a condition to become true."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            time.sleep(interval)
        print(f"Timeout waiting for {description} after {timeout}s")
        return False
        # Examples:
        # condition = lambda: datetime.utcnow().second % 10 == 0
        # RetryUtils.wait_for_condition(condition, timeout=5, interval=1, description="even second")
        # -> True or False depending on timing

    @staticmethod
    def measure_execution_time(func: Callable) -> Callable:
        """Decorator to measure function execution time."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = time.time() - start_time
                print(f"{func.__name__} executed in {TimeUtils.format_duration(execution_time)}")
        return wrapper
        # Examples:
        # @RetryUtils.measure_execution_time
        # def slow():
        #     time.sleep(2)
        # slow()
        # -> prints "slow executed in 2.00s"
