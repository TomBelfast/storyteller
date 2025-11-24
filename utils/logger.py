import sys
from loguru import logger

# Remove default handler
logger.remove()

# Add console handler (human readable)
logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")

# Add file handler (serialized JSON for UI)
logger.add("logs/system_events.json", serialize=True, rotation="10 MB", retention="1 day")

# Export logger
__all__ = ["logger"]
