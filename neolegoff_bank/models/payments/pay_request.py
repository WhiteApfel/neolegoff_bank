import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field, root_validator


class PaymentProviderFields(BaseModel):
    ...

    def export_tinkoff_dict(self):
        return {}

    def export_tinkoff_json(self):
        return json.dumps(self.export_tinkoff_dict())


class PaymentParameters(BaseModel):
    payment_type: str
    provider: str
    amount: Decimal
    account: str
    fields: PaymentProviderFields = None
    id: str = Field(default_factory=lambda: str(int(datetime.now().timestamp() * 1000)))
    currency: str = "RUB"
    delay_accepted: bool = False
    front_camera: bool = True
    cellular: str = "WIFI"

    @root_validator(pre=True)
    def pack_fields(cls, values: dict[str, Any]):
        def fields_iterator():
            return cls.__fields__["fields"].type_.__fields__.items()

        if "fields" not in values and all(
            field_name in values for field_name, _ in fields_iterator()
        ):
            values["fields"] = {
                field_name: values[field_name] for field_name, _ in fields_iterator()
            }

        return values

    def export_pay_tinkoff_json(self):
        return json.dumps(
            {
                "provider": self.provider,
                "moneyAmount": str(self.amount.quantize(Decimal(".01"))),
                "userPaymentId": self.id,
                "account": self.account,
                "currency": self.currency,
                "providerFields": self.fields.export_tinkoff_dict(),
                "delayAccepted": str(self.delay_accepted).lower(),
                "frontCamera": str(self.front_camera).lower(),
                "cellularService": self.cellular,
            }
        )

    def export_commissions_json(self):
        return json.dumps(
            {
                "paymentType": self.payment_type,
                "provider": self.provider,
                "moneyAmount": str(self.amount.quantize(Decimal(".01"))),
                "account": self.account,
                "currency": self.currency,
                "providerFields": self.fields.export_tinkoff_dict(),
            }
        )


class PaymentFieldsC2cOut(PaymentProviderFields):
    bank_card: str

    def export_tinkoff_dict(self):
        return {
            "bankCard": self.bank_card,
        }


class PaymentParametersC2cOut(PaymentParameters):
    account: str
    amount: Decimal
    bank_card: str | None
    fields: PaymentFieldsC2cOut = None
    payment_type: str = "Transfer"
    provider: str = "c2c-out"


class PaymentFieldsMobileProvider(PaymentProviderFields):
    phone: str

    def export_tinkoff_dict(self):
        return {
            "phone": self.phone,
        }


class PaymentParametersMobileProvider(PaymentParameters):
    provider: Literal["mts", "tele2", "beeline"] | str
    account: str
    amount: Decimal
    phone: str | None
    fields: PaymentFieldsMobileProvider = None
    payment_type: str = "Payment"


class PaymentFieldsSbpQr(PaymentProviderFields):
    merchant_name: str
    merchant_display_name: str
    qr_id: str
    mcc: str

    def export_tinkoff_dict(self):
        return {
            "merchantDisplayName": self.merchant_display_name,
            "qrId": self.qr_id,
            "mcc": self.mcc,
            "merchantName": self.merchant_name,
        }


class PaymentParametersSbpQr(PaymentParameters):
    provider: Literal["qr-pay"] = "qr-pay"
    account: str
    amount: Decimal
    merchant_name: str
    merchant_display_name: str
    qr_id: str
    mcc: str
    fields: PaymentFieldsSbpQr = None
    payment_type: str = "Payment"
