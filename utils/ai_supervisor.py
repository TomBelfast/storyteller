import functools
import time
from utils.logger import logger

def ai_supervisor(retry_count=3, delay=2):
    """
    Decorator for AI functions.
    - Catches exceptions.
    - Logs args/kwargs context.
    - Retries execution.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < retry_count:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    logger.exception(
                        f"Error in {func.__name__} (Attempt {attempts}/{retry_count})",
                        context={
                            "args": [str(a) for a in args],
                            "kwargs": {k: str(v) for k, v in kwargs.items()},
                            "error": str(e)
                        }
                    )
                    if attempts == retry_count:
                        logger.critical(f"Permanent failure in {func.__name__} after {retry_count} attempts.")
                        raise e
                    time.sleep(delay)
        return wrapper
    return decorator
