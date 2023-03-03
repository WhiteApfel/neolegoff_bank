from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, Field


class AuthNextStepResponse(BaseModel):
    action: str
    step: str
    cid: str
    collect_fingerprint: Optional[bool] = Field(False, alias="collectFingerprint")
    can_skip: Optional[bool] = Field(False, alias="canSkip")
    error: Optional[str]
    error_message: Optional[str]

    @property
    def is_error(self):
        return self.error is not None


class AuthNextStepSmsResponse(AuthNextStepResponse):
    token: str
    keyboard: str
    length: int
    phone: str


class AuthCompleteResponse(BaseModel):
    code: str
    session_state: str


class AuthTokens(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    id_token: str
    refresh_token: str
    scope: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def is_access_token_alive(self):
        return datetime.utcnow() < self.created_at + timedelta(seconds=self.expires_in)


class ResponseGetCipherKey(BaseModel):
    result: str
    success: bool
