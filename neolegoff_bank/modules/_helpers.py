import uuid
from ssl import SSLWantReadError
from types import UnionType
from typing import Any, TypeVar

from httpx import Response
from pydantic import BaseModel, ValidationError

from neolegoff_bank._service.context_logger import get_context_logger, Context
from neolegoff_bank.exceptions.responses import (
    NeolegoffApiError,
    NeolegoffAuthError,
    NeolegoffBaseResponseError,
    NeolegoffUnauthorizedError,
)
from neolegoff_bank.exceptions.responses.auth import NeolegoffRefreshTokensError
from neolegoff_bank.models.api_response_base import BaseApiResponse, PayloadModel
from neolegoff_bank.models.auth import AuthNextStepResponse

Func = TypeVar("Func")

logger = get_context_logger(__name__)


def pydantic_auto_detect(models: list[type[BaseModel]], data: dict) -> BaseModel:
    for model in models:
        try:
            model_data = model(**data)
            return model_data
        except ValidationError:
            continue
    raise ValueError(f"Data doesn't match any model")


def prepare_response(
    auth_required: bool = True,
    specific_exceptions: list[type[NeolegoffBaseResponseError]] | None = None,
):
    def decorate(f: Func) -> Func:
        async def wrapper(self, *args, **kwargs):  # TODO: Add type hint for self
            logger.debug(
                f"(prepare_response) Call {f.__module__}.{f.__name__} with"
                f" {auth_required=}"
            )
            try:
                if auth_required:
                    logger.debug(
                        "(prepare_response) Auth required. Access token status:"
                        f" alive={self.core.tokens.is_access_token_alive}"
                    )
                    if not self.core.tokens.is_access_token_alive:
                        await self._neolegoff.auth.authorize()

                try:
                    response: Response | Any = await f(self, *args, **kwargs)
                except (SSLWantReadError,) as e:
                    response: Response | Any = await f(self, *args, **kwargs)

                if not isinstance(response, Response):
                    logger.debug(
                        "(prepare_response) Result is not Response, return raw"
                    )
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
                                result = payload_model(payload=model.payload)
                                logger.debug(
                                    (
                                        "(prepare_response) Result is success and"
                                        f" match {result.__class__.__name__}"
                                    ),
                                    extra={"result": result.dict()},
                                )
                                return result
                        elif issubclass(type(return_type), UnionType):
                            try:
                                model = pydantic_auto_detect(
                                    return_type.__args__, response.json()
                                )
                                logger.debug(
                                    "(prepare_response) Model is autodetect"
                                    f" {model.__class__.__name__} from"
                                    f" {return_type.__args__}"
                                )
                                return model
                            except ValueError:
                                logger.debug(
                                    "(prepare_response) Except ValueError from"
                                    " autodetect"
                                )
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

                        logger.debug(
                            (
                                "(prepare_response) Result is success"
                                f" {model.__class__.__name__}"
                            ),
                            extra={"result": model.dict()},
                        )

                        return model

                    return response

                if specific_exceptions is not None:
                    for exc in specific_exceptions:
                        if exc.error_models is None:
                            raise ValueError(
                                "Specific exception mut have error_models."
                                f" {exc.__name__} doesn't contain error_models."
                            )
                        for error_model in exc.error_models:
                            try:
                                data = error_model(**response.json())
                                raise exc(response, args=args, kwargs=kwargs, data=data)
                            except ValidationError:
                                logger.debug(
                                    (
                                        f"Model {error_model.__name__} doesn't match"
                                        f" {response.text}"
                                    ),
                                    extra={
                                        "matching": {
                                            "model": error_model.__name__,
                                            "response_data": "",
                                        }
                                    },
                                )

                if response.status_code == 403:
                    raise NeolegoffUnauthorizedError(
                        response=response, args=args, kwargs=kwargs
                    )

                error = NeolegoffBaseResponseError(
                    response=response, args=args, kwargs=kwargs
                )
                raise error

            except NeolegoffRefreshTokensError as e:
                if e.data.need_new_auth:
                    self._neolegoff.core.tokens = None
                    self._neolegoff.core.session_info = None
                    self._neolegoff.core.cookies = None
                    logger.error(
                        "(prepare_response) Refresh token error. Tokens"
                        " have been reset. Re-login required."
                    )
                else:
                    logger.error(
                        "(prepare_response) Refresh token error:"
                        f" {e.data.error}. Attempts left:"
                        f" {e.data.attempts_left}"
                    )
                raise

            except:
                logger.exception("Exception during prepare response")
                raise

        return wrapper

    return decorate
