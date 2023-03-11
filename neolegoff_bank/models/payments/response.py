from decimal import Decimal
from typing import Any

from pydantic import Field, root_validator

from neolegoff_bank.models import Amount
from neolegoff_bank.models.api_response_base import BaseApiResponse, PayloadModel


class CommissionInfo(PayloadModel):
    min_amount: Decimal = Field(..., alias="minAmount")
    max_amount: Decimal = Field(..., alias="maxAmount")
    limit: Decimal = Field(..., alias="limit")

    amount: Amount = Field(..., alias="total")
    commission_amount: Amount = Field(..., alias="value")

    short_description: str = Field(..., alias="shortDescription")
    description: str = Field(..., alias="description")

    is_unfinished: bool = Field(..., alias="unfinishedFlag")
    external_fees: list[Any] = Field(..., alias="externalFees")
    provider_id: str = Field(..., alias="providerId")


class PaymentInfo(PayloadModel):
    payment_id: str = Field(..., alias="paymentId")

    amount: Amount = Field(..., alias="amount")
    commission_amount: Amount = Field(..., alias="commission")
    total_amount: Amount = Field(..., alias="amountWithCommission")

    fields: dict = Field(..., alias="extraFields")
    # commission_info_helper: dict = Field(..., alias="commissionInfo")

    @root_validator(pre=True)
    def normalize_info(cls, values):
        return values | values.get("payload", {}).get("commissionInfo", {})


class ConfirmationInfo(BaseApiResponse):
    payload: None = None
    operation_ticket: str = Field(..., alias="operationTicket")
    operation_type: str = Field(..., alias="initialOperation")
    confirmations: list[str]
    confirmation_data: dict = Field(..., alias="confirmationData")
