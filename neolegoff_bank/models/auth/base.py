from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, Field


class AuthNextStepResponse(BaseModel):
    action: str
    step: str
    cid: str
    collect_fingerprint: bool | None = Field(False, alias="collectFingerprint")
    can_skip: bool | None = Field(False, alias="canSkip")
    error: str | None = None
    error_message: str | None = None

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


class RefreshTokensError(BaseModel):
    error: str
    need_new_auth: bool
    attempts_left: int
