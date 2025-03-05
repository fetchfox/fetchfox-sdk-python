import logging
from .client import FetchFox

logger = logging.getLogger("fetchfox")
logger.setLevel(logging.WARNING)
logger.addHandler(logging.NullHandler())

__version__ =  "0.1.0"
__all__ = ["FetchFox"]