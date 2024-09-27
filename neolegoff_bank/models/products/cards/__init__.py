from datetime import date, datetime
from typing import Any

from pydantic import model_validator, BaseModel, Field

from neolegoff_bank.models.base import Amount


class CardBase(BaseModel):
    id: str
    name: str
    value: str
    primary: bool
    is_frozen: bool = Field(alias="frozenCard")
    is_activated: bool = Field(alias="activated")
    available_amount: Amount = Field(alias="availableBalance")
    creation_date: date

    position: int
    payment_system: str = Field(..., alias="paymentSystem")
    design: str = Field(alias="cardDesign")

    _raw: dict[str, Any]

    @model_validator(mode="before")
    @classmethod
    def root_base(cls, values: dict):
        values["_raw"] = values.copy()
        if "expiration" in values:
            expiration_date = values.get("expiration").get("milliseconds")
            values["expiration_date"] = datetime.fromtimestamp(
                expiration_date / 1000
            ).date()

        creation_ms = values.get("creationDate").get("milliseconds")
        values["creation_date"] = datetime.fromtimestamp(creation_ms / 1000).date()
        return values


class CardInternal(CardBase):
    expiration_date: date


class CardExternal(CardBase):
    ...
