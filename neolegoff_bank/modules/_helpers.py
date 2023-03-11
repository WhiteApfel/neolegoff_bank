from ssl import SSLWantReadError
from types import UnionType
from typing import Any, TypeVar

from httpx import Response
from pydantic import BaseModel, ValidationError

from neolegoff_bank.exceptions.responses import (
    NeolegoffApiError,
    NeolegoffAuthError,
    NeolegoffBaseResponseError,
    NeolegoffUnauthorizedError,
)
from neolegoff_bank.models.api_response_base import BaseApiResponse, PayloadModel
from neolegoff_bank.models.auth import AuthNextStepResponse

Func = TypeVar("Func")


def pydantic_auto_detect(models: list[type[BaseModel]], data: dict) -> BaseModel:
    for model in models:
        try:
            model_data = model(**data)
            return model_data
        except ValidationError:
            continue
    print(models, data)
    raise ValueError(f"Data doesn't match any model")


def prepare_response(auth_required: bool = True):
    def decorate(f: Func) -> Func:
        async def wrapper(self, *args, **kwargs):  # TODO: Add type hint for self
            if auth_required:
                if not self.core.tokens.is_access_token_alive:
                    await self._neolegoff.auth.authorize()

            try:
                response: Response | Any = await f(self, *args, **kwargs)
            except (SSLWantReadError,) as e:
                response: Response | Any = await f(self, *args, **kwargs)

            if not isinstance(response, Response):
                return response

            if response.is_success:
                return_type = f.__annotations__["return"]

                if "neolegoff_bank.models" in repr(
                    return_type
                ):  # return type is neolegoff model
                    if issubclass(type(return_type), type) and issubclass(
                        return_type, PayloadModel
                    ):  # extract payload from response model
                        model = BaseApiResponse(**response.json())

                        if model.is_success:
                            payload_model = f.__annotations__["return"]
                            return payload_model(payload=model.payload)
                    elif issubclass(type(return_type), UnionType):
                        try:
                            model = pydantic_auto_detect(
                                return_type.__args__, response.json()
                            )
                        except ValueError:
                            model = return_type(**response.json())
                    else:
                        model = return_type(**response.json())

                    if isinstance(model, AuthNextStepResponse) and model.is_error:
                        raise NeolegoffAuthError(
                            response=response,
                            args=args,
                            kwargs=kwargs,
                        )

                    if isinstance(model, BaseApiResponse) and not model.is_success:
                        raise NeolegoffApiError(
                            response=response,
                            args=args,
                            kwargs=kwargs,
                            model=model,
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
