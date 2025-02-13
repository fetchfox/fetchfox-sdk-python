import logging
from .client import FetchFoxSDK
from .workflow import Workflow

logger = logging.getLogger("fetchfox")
logger.setLevel(logging.WARNING)
logger.addHandler(logging.NullHandler())

__version__ = "0.0.2"
__all__ = ["FetchFoxSDK","Workflow"]