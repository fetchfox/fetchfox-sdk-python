import logging
from .client import FetchFox
from .workflow import Workflow
from .item import Item

logger = logging.getLogger("fetchfox")
logger.setLevel(logging.WARNING)
logger.addHandler(logging.NullHandler())

__version__ =  "0.3.0"
__all__ = ["FetchFox", "Workflow", "Item"]