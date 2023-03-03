from decimal import Decimal

from pydantic import BaseModel, Field


class Currency(BaseModel):
    code: int
    name: str
    str_code: str = Field(..., alias="strCode")


class Amount(BaseModel):
    currency: Currency
    value: Decimal
