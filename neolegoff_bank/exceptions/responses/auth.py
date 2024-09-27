from typing import Any

from httpx import Response
from pydantic import BaseModel

from neolegoff_bank.exceptions.responses.base import NeolegoffBaseResponseError
from neolegoff_bank.models.auth import RefreshTokensError


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


class NeolegoffRefreshTokensError(NeolegoffBaseResponseError):
    error_models: list[type[BaseModel]] | None = [RefreshTokensError]

    def __init__(
        self,
        response: Response,
        data: RefreshTokensError,
        args: list[Any] = None,
        kwargs: dict[str, Any] = None,
    ):
        self.data = data
        super().__init__(response, args, kwargs)

    @property
    def exception_message(self):
        return str(self.data)


__all__ = [NeolegoffUnauthorizedError, NeolegoffAuthError]
