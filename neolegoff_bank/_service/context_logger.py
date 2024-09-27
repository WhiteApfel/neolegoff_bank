import logging
from contextvars import ContextVar
from typing import Any

from pythonjsonlogger import jsonlogger

Context: ContextVar[dict[str, Any]] = ContextVar("context", default={})


class ContextAdapter(logging.LoggerAdapter):
    def process(self, msg: str, kwargs: Any) -> tuple[str, Any]:
        try:
            context = Context.get()
        except LookupError:
            return msg, kwargs

        for key, value in context.items():
            kwargs.setdefault("extra", {})[key] = value
        return msg, kwargs


def get_context_logger(name: str) -> ContextAdapter:
    return ContextAdapter(logging.getLogger(name), {})
