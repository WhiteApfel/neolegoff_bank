from typing import Any

from pydantic import BaseModel, Field


class PayloadModel(BaseModel):
    ...


class BaseApiResponse(BaseModel):
    result_code: str = Field(..., alias="resultCode")
    tracking_id: str = Field(..., alias="trackingId")
    payload: dict[str, Any] | list[dict[str, Any]] | None

    @property
    def is_success(self) -> bool:
        return self.result_code == "OK"
