from typing import Any

from httpx import Response

from neolegoff_bank.exceptions.responses.base import NeolegoffBaseResponseError


class NeolegoffUnauthorizedError(NeolegoffBaseResponseError):
    def __init__(
        self,
        response: Response,
        args: list[Any] = None,
        kwargs: dict[str, Any] = None,
    ):
        super().__init__(response, args, kwargs)


class NeolegoffAuthError(NeolegoffBaseResponseError):
    def __init__(
        self,
        response: Response,
        args: list[Any] = None,
        kwargs: dict[str, Any] = None,
    ):
        super().__init__(response, args, kwargs)


__all__ = [NeolegoffUnauthorizedError, NeolegoffAuthError]
