from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, root_validator

from neolegoff_bank.models.api_response_base import PayloadModel
from neolegoff_bank.models.base import Amount, Location


class FieldsValues(BaseModel):
    receiver_bank_name: str | None = Field(None, alias="receiverBankName")
    masked_fio: str | None = Field(None, alias="maskedFio")
    pointer: str | None
    operation_id: str | None = Field(None, alias="operationId")
    message_id: str | None = Field(None, alias="messageId")
    bank_member_id: str | None = Field(None, alias="bankMemberId")
    ig_bill_id: str | None = Field(None, alias="igBillId")
    confirmation_code: str | None = Field(None, alias="confirmationCode")
    order_id: str | None = Field(None, alias="orderId")
    qr_id: int | None = Field(None, alias="qrId")
    merchant_display_name: str | None = Field(None, alias="merchantDisplayName")
    mcc: int | None
    merchant_name: str | None = Field(None, alias="merchantName")
    agreement: str | None
    credit_agreement: str | None = Field(None, alias="creditAgreement")
    requirement_type: int | None = Field(None, alias="requirementType")
    ci_amount: str | None = Field(None, alias="ciAmount")
    ci_currency: int | None = Field(None, alias="ciCurrency")
    product_specify_type: str | None = Field(None, alias="productSpecifyType")
    joint_id: str | None = Field(None, alias="jointId")
    recipient_type: str | None = Field(None, alias="recipientType")
    description: str | None
    transaction_id: str | None = Field(None, alias="transactionId")
    pointer_type: str | None = Field(None, alias="pointerType")
    workflow_type: str | None = Field(None, alias="workflowType")
    pointer_link_id: str | None = Field(None, alias="pointerLinkId")
    phone: str | None
    bank_contract: str | None = Field(None, alias="bankContract")


class Payment(BaseModel):
    is_qr: bool = Field(alias="sourceIsQr")
    bank_account_id: str = Field(alias="bankAccountId")
    id: str = Field(alias="paymentId")
    group: str = Field(alias="providerGroupId")
    type: str = Field(alias="paymentType")
    fee_amount: Amount | None = Field(None, alias="feeAmount")
    provider_id: str = Field(alias="providerId")
    has_payment_order: bool = Field(alias="hasPaymentOrder")
    comment: str
    fields_values: FieldsValues = Field(alias="fieldsValues")
    is_repeatable: bool = Field(alias="repeatable")
    card_number: str = Field(alias="cardNumber")
    template_id: int | None = Field(None, alias="templateId")
    template_is_favorite: bool | None = Field(None, alias="templateIsFavorite")


class Category(BaseModel):
    id: str | int
    name: str


class Brand(BaseModel):
    name: str
    id: str | int
    link: str | None


class SpendingCategory(BaseModel):
    name: str
    icon: str
    id: int


class OperationMinimal(BaseModel):
    is_dispute: bool = Field(False, alias="isDispute")
    is_offline: bool = Field(alias="isOffline")
    is_hce: bool = Field(alias="isHce")
    has_statement: bool = Field(alias="hasStatement")
    id: str
    type: Literal["Debit", "Credit"]
    locations: list[Location]
    description: str
    status: Literal["OK", "FAILED"]
    spending_category: SpendingCategory = Field(alias="spendingCategory")
    amount: Amount
    account_amount: Amount = Field(alias="accountAmount")
    cashback_amount: Amount = Field(alias="cashbackAmount")
    mcc: str = Field(alias="mccString")
    is_card_present: bool = Field(alias="cardPresent")
    is_external_card: bool = Field(alias="isExternalCard")
    category: Category
    created_at: datetime

    raw: dict[str, Any] = Field(exclude=True, repr=False)

    @root_validator(pre=True)
    def add_raw(cls, values: dict):
        values["raw"] = values.copy()
        operation_ms = values.get("operationTime").get("milliseconds")
        values["created_at"] = datetime.fromtimestamp(operation_ms / 1000)
        if "debitingTime" in values:
            expiration_date = values.get("debitingTime").get("milliseconds")
            values["debited_at"] = datetime.fromtimestamp(expiration_date / 1000)
        return values


class OperationBase(OperationMinimal):
    payment: Payment | None
    authorization_id: str | None = Field(None, alias="authorizationId")
    operation_payment_type: str | None = Field(alias="operationPaymentType")
    id_source_type: str = Field(alias="idSourceType")
    group: str | None
    subgroup: Category | None
    pos_id: str | None = Field(None, alias="posId")
    message: str | None
    sender_details: str | None
    card_number: str | None = Field(None, alias="cardNumber")
    card_id: str | None = Field(alias="card")
    compensation: str | None
    point_of_sale_id: int | None = Field(None, alias="pointOfSaleId")
    brand: Brand | None
    debited_at: datetime | None

    @property
    def is_pay(self):
        return self.group is not None and self.group == "PAY"

    @property
    def is_income(self):
        return self.group is not None and self.group == "INCOME"

    @property
    def is_transfer(self):
        return self.group is not None and self.group == "TRANSFER"


class Operations(PayloadModel):
    operations: list[OperationBase] = Field(alias="payload")

    def __iter__(self):
        return iter(self.operations)

    def __len__(self):
        return len(self.operations)
