from typing import Literal, Optional

from pydantic import BaseModel, Field

from neolegoff_bank.models.api_response_base import BaseApiResponse, PayloadModel


class DeviceAuthorizeResponsePayload(PayloadModel):
    session_id: str = Field(..., alias="sessionid")
    access_level: Literal["CANDIDATE", "CLIENT"] = Field(..., alias="accessLevel")
    prompts: list[str]
    client_type: Optional[str] = Field(None, alias="clientType")
    user_id: str = Field(..., alias="userId")
    sso_id: str = Field(..., alias="ssoId")
    is_client: bool = Field(..., alias="isClient")


class DeviceAuthorizeResponse(BaseApiResponse):
    payload: DeviceAuthorizeResponsePayload


class AuthSetPinResponsePayload(BaseModel):
    key: str


class AuthSetPinResponse(BaseApiResponse):
    payload: AuthSetPinResponsePayload
