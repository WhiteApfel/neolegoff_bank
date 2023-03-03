from typing import Any

from httpx import Response

from neolegoff_bank.models.api_response_base import BaseApiResponse


class NeolegoffBaseResponseError(BaseException):
    def __init__(
        self,
        response: Response,
        args: list[Any] = None,
        kwargs: dict[str, Any] = None,
        *exc_args,
        **exc_kwargs
    ):
        self.response: Response = response
        self.args: list[Any] = args
        self.kwargs: dict[str, Any] = kwargs

    @property
    def status_code(self) -> int:
        return self.response.status_code

    @property
    def is_json(self) -> bool:
        content_type = self.response.headers.get("Content-Type")
        if not content_type:
            return False
        return "application/json" in content_type

    @property
    def json(self) -> dict | None:
        return None if not self.is_json else self.response.json()


class NeolegoffApiError(NeolegoffBaseResponseError):
    def __init__(
        self,
        response: Response,
        args: list[Any] = None,
        kwargs: dict[str, Any] = None,
        model: BaseApiResponse | None = None,
    ):
        super().__init__(response, args, kwargs)
        self.model: BaseApiResponse | None = model
