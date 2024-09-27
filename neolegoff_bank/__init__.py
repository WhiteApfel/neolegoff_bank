import logging.config

from ._service import LOGGING
from .modules import AioNeolegoff


logging.config.dictConfig(LOGGING)
