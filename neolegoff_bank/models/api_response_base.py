from typing import Any

from pydantic import BaseModel, Field, root_validator


class PayloadModel(BaseModel):
    ...

    @root_validator(pre=True)
    def unpack_fields(cls, values: dict[str, Any]):
        def fields_iterator():
            return cls.__fields__.items()

        payload = values.get("payload", {})

        for field_name, field_info in fields_iterator():
            if field_info.alias in payload:
                values[field_info.alias] = payload.get(field_info.alias)

        return values


class BaseApiResponse(BaseModel):
    result_code: str = Field(..., alias="resultCode")
    tracking_id: str = Field(..., alias="trackingId")
    payload: dict[str, Any] | list[dict[str, Any]] | None

    is_business_error: bool = Field(False, alias="isBusinessError")
    error_message: str | None = Field(None, alias="plainMessage")

    @property
    def is_success(self) -> bool:
        return self.result_code == "OK"
