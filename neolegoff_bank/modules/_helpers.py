from typing import Any, TypeVar

from httpx import Response

from neolegoff_bank.exceptions.responses import (
    NeolegoffApiError,
    NeolegoffAuthError,
    NeolegoffBaseResponseError,
    NeolegoffUnauthorizedError,
)
from neolegoff_bank.models.api_response_base import BaseApiResponse, PayloadModel
from neolegoff_bank.models.auth import AuthNextStepResponse

Func = TypeVar("Func")


def prepare_response(auth_required: bool = True):
    def decorate(f: Func) -> Func:
        async def wrapper(self, *args, **kwargs):  # TODO: Add type hint for self
            if auth_required:
                if not self.core.tokens.is_access_token_alive:
                    await self.auth.auth_authorize()

            response: Response | Any = await f(self, *args, **kwargs)
            if not isinstance(response, Response):
                return response

            if response.is_success:
                if "neolegoff_bank.models" in repr(
                    f.__annotations__["return"]
                ):  # return type is neolegoff model
                    if issubclass(
                        f.__annotations__["return"], PayloadModel
                    ):  # extract payload from response model
                        model = BaseApiResponse(**response.json())

                        if model.is_success:
                            return f.__annotations__["return"](payload=model.payload)

                    else:
                        model = f.__annotations__["return"](**response.json())

                    if isinstance(model, AuthNextStepResponse) and model.is_error:
                        raise NeolegoffAuthError(
                            response=response, args=args, kwargs=kwargs
                        )

                    if isinstance(model, BaseApiResponse) and not model.is_success:
                        raise NeolegoffApiError(
                            response=response, args=args, kwargs=kwargs, model=model
                        )

                    return model

                return response

            if response.status_code == 403:
                raise NeolegoffUnauthorizedError(
                    response=response, args=args, kwargs=kwargs
                )

            raise NeolegoffBaseResponseError(
                response=response, args=args, kwargs=kwargs
            )

        return wrapper

    return decorate
