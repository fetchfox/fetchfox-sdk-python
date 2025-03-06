import logging
from .client import FetchFox
from .workflow import Workflow
from .result_item import ResultItem

logger = logging.getLogger("fetchfox")
logger.setLevel(logging.WARNING)
logger.addHandler(logging.NullHandler())

__version__ =  "0.2.0"
__all__ = ["FetchFox", "Workflow", "ResultItem"]